import sys
import os
import tempfile
import subprocess
import re

def clean_code_snippet(code: str) -> str:
    """Removes markdown code fences (```python ... ```) if present in LLM response string."""
    if not code:
        return ""
    code = re.sub(r"^```python\s*", "", code, flags=re.MULTILINE)
    code = re.sub(r"^```\s*", "", code, flags=re.MULTILINE)
    # Unescape only fully-escaped one-line snippets; otherwise "\n" inside string literals would be broken
    if "\\n" in code and "\n" not in code:
        code = re.sub(r':\\n\s*', ':\n    ', code)
        code = re.sub(r'\\n(?=[ \t]*(?:#|def |class |return |if |else|elif |for |while |import |from |try|except|with |pass|[a-zA-Z_]\w*\s*=))', '\n', code)
        code = code.replace('\\n', '\n')
    return code.strip()

SANDBOX_HIDDEN_DIRS = {"exercises"}  # generated module outputs must not leak into the sandbox


def _link_dir(src: str, dst: str):
    """Mirrors a fixture folder as real folders holding one symlink per file: reads hit the originals without
    copying (image sets can be 100s of MB), while files the generated code creates or deletes stay in the sandbox.
    Opening a linked file for writing would still change the original; generated code only reads fixtures."""
    import shutil
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SANDBOX_HIDDEN_DIRS]
        target = os.path.join(dst, os.path.relpath(root, src))
        os.makedirs(target, exist_ok=True)
        for name in files:
            link = os.path.join(target, name)
            if os.path.lexists(link):
                continue
            try:
                os.symlink(os.path.abspath(os.path.join(root, name)), link)
            except OSError:
                # shortcut: Windows without symlink rights copies instead; fine for small local test runs only
                shutil.copy2(os.path.join(root, name), link)


def _mirror_dir(src: str, dst: str):
    """Copies src's top-level files into dst and links its subfolders (except hidden ones)."""
    import shutil
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        src_path = os.path.join(src, name)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, os.path.join(dst, name))
        elif name not in SANDBOX_HIDDEN_DIRS:
            _link_dir(src_path, os.path.join(dst, name))


def describe_sandbox_fixtures(src: str) -> str:
    """Prompt text describing exactly what run_in_sandbox exposes from `src`: files, folders and CSV columns."""
    import csv
    if not src or not os.path.isdir(src):
        return "SANDBOX FIXTURES: none."
    entries = sorted(os.listdir(src))
    files = [f for f in entries if os.path.isfile(os.path.join(src, f))]
    lines = [
        "SANDBOX FIXTURES (the current working directory when solution and tests run):",
        f"- Files (open by bare filename): {', '.join(files) or 'none'}",
    ]
    for name in entries:
        path = os.path.join(src, name)
        if not os.path.isdir(path) or name in SANDBOX_HIDDEN_DIRS:
            continue
        for sub in [name] + sorted(f"{name}/{d}" for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))):
            sub_path = os.path.join(src, sub)
            children = sorted(os.listdir(sub_path))
            subdirs = [c for c in children if os.path.isdir(os.path.join(sub_path, c))]
            leaf_files = [c for c in children if not os.path.isdir(os.path.join(sub_path, c))]
            if subdirs:
                example = next((os.listdir(os.path.join(sub_path, d)) for d in subdirs if os.listdir(os.path.join(sub_path, d))), [])
                lines.append(f"- Folder {sub}/: {len(subdirs)} subfolders (e.g. {', '.join(subdirs[:3])}), "
                             f"each with files like {sub}/{subdirs[0]}/{example[0] if example else '...'}")
            elif leaf_files and sub != name:
                lines.append(f"- Folder {sub}/: {len(leaf_files)} files, e.g. {sub}/{leaf_files[0]}")
    for name in files:
        if name.endswith(".csv"):
            with open(os.path.join(src, name), newline="", encoding="utf-8", errors="replace") as f:
                rows = list(zip(range(2), csv.reader(f)))
            if len(rows) == 2:
                example = ", ".join(f"{col}={val[:110]!r}" for col, val in zip(rows[0][1], rows[1][1]))
                lines.append(f"- {name} columns with first-row values: {example}")
    if not os.path.isabs(src):
        lines.append(f"- Paths starting with {os.path.normpath(src).replace(os.sep, '/')}/ in those files resolve as written.")
    lines.append("Use only these real files; never invent placeholder paths or sub-folders such as 'fixtures/'.")
    return "\n".join(lines)


def run_in_sandbox(
    solution_code: str, 
    unit_test_code: str, 
    module_id: str = None, 
    artifact_sources: list = None,
    timeout: int = 120
) -> tuple[bool, str]:
    """
    Executes generated solution code and unit test code inside an isolated subprocess sandbox.
    Returns (success: bool, execution_log: str).
    """
    import shutil
    solution_code = clean_code_snippet(solution_code)
    unit_test_code = clean_code_snippet(unit_test_code)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy any provided artifact source files/directories into temp_dir
        if artifact_sources:
            for src in artifact_sources:
                if src and os.path.exists(src):
                    if os.path.isdir(src):
                        _mirror_dir(src, temp_dir)  # e.g. results.csv + images/dataset_sample/<class>/
                        # Phase 1 CSVs store paths relative to the run's cwd (./outputs/<run>/images/...)
                        if not os.path.isabs(src):
                            _mirror_dir(src, os.path.join(temp_dir, os.path.normpath(src)))
                    elif os.path.isfile(src):
                        shutil.copy2(src, os.path.join(temp_dir, os.path.basename(src)))

        # 1. Standard solution.py
        sol_path = os.path.join(temp_dir, "solution.py")
        with open(sol_path, "w", encoding="utf-8") as f:
            f.write(solution_code)

        # 2. Module-named solution file if module_id provided
        if module_id:
            clean_id = module_id.lower().replace("-", "_").replace(" ", "_")
            mod_sol_path = os.path.join(temp_dir, f"{clean_id}_solution.py")
            if not os.path.exists(mod_sol_path):
                with open(mod_sol_path, "w", encoding="utf-8") as f:
                    f.write(solution_code)

        # 3. Detect any imported *_solution names in unit test code and create alias files
        for match in re.finditer(r"(?:from|import)\s+([a-zA-Z0-9_]+_solution)", unit_test_code):
            imported_mod = match.group(1)
            imported_path = os.path.join(temp_dir, f"{imported_mod}.py")
            if not os.path.exists(imported_path):
                with open(imported_path, "w", encoding="utf-8") as f:
                    f.write(solution_code)

        # Inject solution import if not explicitly present
        test_content = unit_test_code
        if "from solution import" not in test_content and "import solution" not in test_content and "_solution import" not in test_content:
            test_content = f"from solution import *\n\n{test_content}"

        test_path = os.path.join(temp_dir, "test_runner.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content)

        env = os.environ.copy()
        env["PYTHONPATH"] = temp_dir + os.pathsep + env.get("PYTHONPATH", "")

        try:
            res = subprocess.run(
                [sys.executable, test_path],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if res.returncode == 0:
                return True, res.stdout or "Sandbox Verification Passed"
            else:
                err_log = (res.stderr or res.stdout or "Process returned non-zero exit status").strip()
                return False, err_log

        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Sandbox Execution Error: {str(e)}"
