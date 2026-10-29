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
# Phase 1 checkpoints (e.g. models/sam_vit_b.pth) live in the job's working directory, outside the run folder;
# they are linked into the sandbox at the same relative path so DL exercises can load them.
SANDBOX_MODEL_DIR = "models"
SANDBOX_MAX_IMAGES = 8  # deep-learning steps run on a subset: the sandbox has 120 s and vLLM holds the GPUs

# Runs every test in test_runner.py separately, so one failure no longer hides the rest. Output is unittest's
# "ERROR: test_x" / "FAIL: test_x" blocks, which generation_trace.attribute_failures parses per test.
# Module-level code (imports, top-level asserts) runs on import; a failure there is a whole-script error.
_HARNESS = '''import inspect, sys, unittest
import test_runner


class _Fn(unittest.FunctionTestCase):
    def __str__(self):
        return self._testFunc.__name__


class _Result(unittest.TextTestResult):
    def startTest(self, test):
        print(f"RUNNING {str(test).split()[0]}", file=sys.stderr, flush=True)  # names the test if the run times out
        super().startTest(test)


suite = unittest.defaultTestLoader.loadTestsFromModule(test_runner)
suite.addTests(_Fn(f) for n, f in vars(test_runner).items()
               if n.startswith("test_") and inspect.isfunction(f) and f.__module__ == "test_runner")
sys.exit(0 if unittest.TextTestRunner(resultclass=_Result, verbosity=0).run(suite).wasSuccessful() else 1)
'''


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
    """Prompt text describing exactly what run_in_sandbox exposes from `src`: files, folders, CSV columns and counts."""
    import csv
    import itertools
    from collections import Counter
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
                reader = csv.reader(f)
                header, rows = next(reader, None), list(itertools.islice(reader, 100_000))
            if header and rows:
                # Full values: a cut-off path ('..._mask_2026.p') gets copied by the model as a real path
                example = ", ".join(f"{col}={val!r}" if len(val) <= 300 else f"{col}={val[:80]!r}... ({len(val)} chars, cut)"
                                    for col, val in zip(header, rows[0]))
                lines.append(f"- {name} ({len(rows)} rows) columns with first-row values: {example}")
                # Category counts, so contracts and tests only assume minority classes / thresholds the data has
                for i, col in enumerate(header):
                    counts = Counter(r[i] for r in rows if i < len(r))
                    lo, hi = min(counts.values(), default=0), max(counts.values(), default=0)
                    if 2 <= len(counts) <= 50 and hi > 1:  # categories, not IDs or paths
                        lines.append(f"  - {col}: {len(counts)} distinct values, {lo}-{hi} rows each")
    if not os.path.isabs(src):
        lines.append(f"- Paths starting with {os.path.normpath(src).replace(os.sep, '/')}/ in those files resolve as written.")
    if os.path.isdir(SANDBOX_MODEL_DIR):
        checkpoints = sorted(os.path.relpath(os.path.join(root, f)).replace(os.sep, "/")
                             for root, _, names in os.walk(SANDBOX_MODEL_DIR) for f in names)
        lines.append(f"- Trained Phase 1 model checkpoints (load by this exact path): {', '.join(checkpoints[:10]) or 'none'}")
    lines.append("Use only these real files; never invent placeholder paths such as 'path_to_checkpoint.pth' or sub-folders such as 'fixtures/'.")
    lines.append("Thresholds, filters and expected counts in contracts and tests must be satisfiable with the counts above; "
                 "compute them from the data instead of hardcoding.")
    lines.append(f"SANDBOX LIMITS: the whole test file must finish in 120 s, possibly on CPU. Any step that runs a neural network "
                 f"(DINOv2, SAM, torch models) must process at most {SANDBOX_MAX_IMAGES} images in the tests and by default in "
                 f"the pipeline function (e.g. a `max_images: int = {SANDBOX_MAX_IMAGES}` parameter); load each model once, "
                 f"at module level in the tests.")
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
        if os.path.isdir(SANDBOX_MODEL_DIR):
            _link_dir(SANDBOX_MODEL_DIR, os.path.join(temp_dir, SANDBOX_MODEL_DIR))  # links, not copies: checkpoints are 100s of MB

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
        harness_path = os.path.join(temp_dir, "_harness.py")
        with open(harness_path, "w", encoding="utf-8") as f:
            f.write(_HARNESS)

        env = os.environ.copy()
        env["PYTHONPATH"] = temp_dir + os.pathsep + env.get("PYTHONPATH", "")

        try:
            res = subprocess.run(
                [sys.executable, harness_path],
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

        except subprocess.TimeoutExpired as e:
            partial = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
            running = re.findall(r"^RUNNING (\S+)", partial, re.MULTILINE)
            if not running:
                return False, f"Execution timed out after {timeout} seconds"
            return False, f"ERROR: {running[-1]}\n{'-' * 70}\nExecution timed out after {timeout} seconds in {running[-1]}\n"
        except Exception as e:
            return False, f"Sandbox Execution Error: {str(e)}"
