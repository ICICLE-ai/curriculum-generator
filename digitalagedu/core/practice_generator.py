import os
import re
import shutil
import tempfile
import subprocess
from jinja2 import Environment, FileSystemLoader
import sys

class PracticeGenerator:
    def __init__(self, templates_dir, output_dir, config):
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.config = config

        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))

        self.concept_map = {
            "numpy basics": "numpy_basics.py.j2",
            "pandas & matplotlib": "pandas_analytics.py.j2",
            "deep learning foundations": "pytorch_basics.py.j2",
            "interactive image segmentation": "interactive_segmentation.py.j2",
            "pytorch datasets & dataloaders": "image_datasets.py.j2",
            "custom convolutional neural networks": "custom_cnn.py.j2",
            "cnn optimization, regularization & checkpointing": "cnn_optimization.py.j2",
            "transfer learning & backbone benchmarking": "transfer_learning.py.j2",
            "deep learning semantic segmentation & u-net": "semantic_segmentation.py.j2",
            "explainable ai & grad-cam": "explainable_ai.py.j2",
            "image embeddings, clustering & semantic search": "vector_embeddings.py.j2",
            "vision-language models": "vlm_diagnostics.py.j2",
            "capstone integration & gradio deployment": "gradio_deployment.py.j2"
        }
    
    def _parse_template(self, content: str, mode: str) -> str:
        """
        Parses the template to produce either the exercise or the solution file
        """
        if mode == "exercise":
            # Remove the REFERENCE_SOLUTION blocks (including leading indentation)
            content = re.sub(
                 r'^[ \t]*#\s*\[REFERENCE_SOLUTION\].*?^[ \t]*#\s*\[/REFERENCE_SOLUTION\]\n?', 
                '', 
                content, 
                flags=re.DOTALL | re.MULTILINE
            )

            # Keep the content of STUDENT_STARTER blocks but strip the tag
            content = re.sub(
                r'^[ \t]*#\s*\[STUDENT_STARTER\]\n(.*?)\n^[ \t]*#\s*\[/STUDENT_STARTER\]', 
                r'\1', 
                content, 
                flags=re.DOTALL | re.MULTILINE
            )

        elif mode == "solution":
             # Remove the STUDENT_STARTER blocks (including leading indentation)
            content = re.sub(
                r'^[ \t]*#\s*\[STUDENT_STARTER\].*?^[ \t]*#\s*\[/STUDENT_STARTER\]\n?', 
                '', 
                content, 
                flags=re.DOTALL | re.MULTILINE
            )
            # Keep the content of REFERENCE_SOLUTION blocks but strip the tags
            content = re.sub(
                r'^[ \t]*#\s*\[REFERENCE_SOLUTION\]\n(.*?)\n^[ \t]*#\s*\[/REFERENCE_SOLUTION\]', 
                r'\1', 
                content, 
                flags=re.DOTALL | re.MULTILINE
            )

        return content

    def _verify_sandbox(self, solution_code: str, test_code: str, starter_code: str) -> bool:
        """
        Runs both positive and negative passes in a temp directory
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            solution_path = os.path.join(temp_dir, "target_module.py")
            test_path = os.path.join(temp_dir, "test_exercise.py")

            # --- Positive Test ---
            with open(solution_path, "w") as f:
                f.write(solution_code)
            with open(test_path, "w") as f:
                f.write(test_code)

            env = os.environ.copy()
            env["MKL_THREADING_LAYER"] = "GNU"

            pos_run = subprocess.run(
                [sys.executable, test_path],
                env=env,
                 text=True, capture_output=True,
                  cwd=temp_dir
                  )

            if pos_run.returncode != 0:
                print(f"[ERROR] Positive Verification Failed:\n{pos_run.stderr}")
                return False
            
            # --- Negative Test ---
            # Overwrite target_module.py with starter code
            with open(solution_path, "w") as f:
                f.write(starter_code)
                
            neg_run = subprocess.run(
                [sys.executable, test_path],
                env=env,
                capture_output=True,
                text=True, cwd=temp_dir)

            if neg_run.returncode == 0:
                print("[ERROR] Negative Verification Failed: Starter code passed unit tests")
                return False

            return True

    def generate(self, week_distribution, context):
        """
        Generates, verifies, and writes the exercises for each week
        """

        for week_name, activies in week_distribution.items():
            for activity in activies:
                activity_lower = activity.lower()

                # Check concept matches
                for concept, template_name in self.concept_map.items():
                    if concept in activity_lower:
                        print(f"\n[INFO] Found match for {concept} in {week_name}...")

                        try:
                            # Load and render the template
                            master_tpl = self.jinja_env.get_template(template_name)
                            test_tpl = self.jinja_env.get_template(f"test_{template_name}")

                            rendered_master = master_tpl.render(context)
                            rendered_test = test_tpl.render(context)

                            # Parse starter vs solution
                            exercise_code = self._parse_template(rendered_master, "exercise")
                            solution_code = self._parse_template(rendered_master, "solution")

                            # Verify
                            if self._verify_sandbox(solution_code, rendered_test, exercise_code):
                                # 4. Export on success
                                week_folder = os.path.join(self.output_dir, "exercises", week_name)
                                os.makedirs(week_folder, exist_ok=True)
                                
                                template_base = template_name.replace(".py.j2", "")
                                with open(os.path.join(week_folder, f"{template_base}_exercise.py"), "w") as f:
                                    f.write(exercise_code)
                                with open(os.path.join(week_folder, f"{template_base}_solution.py"), "w") as f:
                                    f.write(solution_code)
                                with open(os.path.join(week_folder, f"{template_base}_test.py"), "w") as f:
                                    f.write(rendered_test)
                                    
                                print(f"[SUCCESS] Exported verified exercise package to {week_folder}")
                            else:
                                print(f"[WARNING] Verification failed for {template_name}. Skipping export.")
                                
                        except Exception as e:
                            print(f"[ERROR] Failed to compile {template_name}: {e}")
