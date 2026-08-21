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
    return code.strip()

def run_in_sandbox(
    solution_code: str, 
    unit_test_code: str, 
    module_id: str = None, 
    timeout: int = 120
) -> tuple[bool, str]:
    """
    Executes generated solution code and unit test code inside an isolated subprocess sandbox.
    Returns (success: bool, execution_log: str).
    """
    solution_code = clean_code_snippet(solution_code)
    unit_test_code = clean_code_snippet(unit_test_code)

    with tempfile.TemporaryDirectory() as temp_dir:
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
