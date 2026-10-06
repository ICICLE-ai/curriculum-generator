import os
import shutil
import tempfile
import unittest
from PIL import Image
import numpy as np

from digitalagedu.core.practice_generator import PracticeGenerator
from digitalagedu.core.concepts_registry import CONCEPT_MAP


class TestRelativePathCurriculum(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.mkdtemp(prefix="digitalagedu_test_")
        self.output_dir = os.path.join(self.temp_root, "output")
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "digitalagedu", "templates"
        )
        
        # Create mock output bundle directory hierarchy
        self.raw_dir = os.path.join(self.output_dir, "images", "raw")
        self.mask_dir = os.path.join(self.output_dir, "images", "masks")
        self.sample_dataset_dir = os.path.join(self.output_dir, "images", "dataset_sample")
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.mask_dir, exist_ok=True)
        os.makedirs(self.sample_dataset_dir, exist_ok=True)
        
        # Create sample raw image
        self.sample_img_name = "sample_test_image.jpg"
        raw_img_path = os.path.join(self.raw_dir, self.sample_img_name)
        img = Image.new("RGB", (64, 64), color="green")
        img.save(raw_img_path)
        
        # Create sample mask image
        self.sample_mask_name = "sample_test_mask.png"
        mask_path = os.path.join(self.mask_dir, self.sample_mask_name)
        mask = Image.new("L", (64, 64), color="white")
        mask.save(mask_path)
        
        # Create sample class subdirectories
        self.classes = ["benign", "malignant"]
        for cls in self.classes:
            cls_dir = os.path.join(self.sample_dataset_dir, cls)
            os.makedirs(cls_dir, exist_ok=True)
            for i in range(5):
                sample_cls_img = os.path.join(cls_dir, f"sample_{i}.jpg")
                Image.new("RGB", (64, 64), color="blue").save(sample_cls_img)
                
        # Create mock results.csv
        results_csv = os.path.join(self.output_dir, "results.csv")
        with open(results_csv, "w", encoding="utf-8") as f:
            f.write("image_path,ground_truth,predicted_class,confidence\n")
            f.write(f"{raw_img_path},benign,benign,0.95\n")
            f.write(f"{raw_img_path},malignant,benign,0.85\n")
            f.write(f"{raw_img_path},benign,benign,0.99\n")
            
        self.context = {
            "subject": "Medical AI",
            "grade": 10,
            "class_mapping": self.classes,
            "image_size": 64,
            "train_split": 0.8,
            "dataset_root": "../../../images/dataset_sample",
            "sample_image_path": f"../../../images/raw/{self.sample_img_name}",
            "sample_mask_path": f"../../../images/masks/{self.sample_mask_name}"
        }
        
    def tearDown(self):
        if os.path.exists(self.temp_root):
            shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_all_templates_sandbox_verification(self):
        """
        Validates that all 12 modules pass dual-pass sandbox verification:
        - Reference solutions pass all assertions
        - Starter code fails assertions
        """
        practice_gen = PracticeGenerator(
            templates_dir=self.templates_dir,
            output_dir=self.output_dir,
            config=None
        )
        
        for concept, template_name in CONCEPT_MAP.items():
            with self.subTest(concept=concept, template=template_name):
                master_tpl = practice_gen.jinja_env.get_template(template_name)
                test_tpl = practice_gen.jinja_env.get_template(f"test_{template_name}")
                
                rendered_master = master_tpl.render(self.context)
                rendered_test = test_tpl.render(self.context)
                
                exercise_code = practice_gen._parse_template(rendered_master, "exercise")
                solution_code = practice_gen._parse_template(rendered_master, "solution")
                
                # Check sandbox verification
                passed = practice_gen._verify_sandbox(solution_code, rendered_test, exercise_code)
                self.assertTrue(
                    passed, 
                    f"Sandbox verification failed for concept '{concept}' (template: {template_name})"
                )

    def test_full_practice_generation_and_export(self):
        """
        Tests generation into Week_01, Week_02, etc., and asserts files exist.
        """
        practice_gen = PracticeGenerator(
            templates_dir=self.templates_dir,
            output_dir=self.output_dir,
            config=None
        )
        
        week_distribution = {
            "Week_01": ["numpy basics", "pandas & matplotlib"],
            "Week_02": ["deep learning foundations", "interactive image segmentation"],
            "Week_03": ["pytorch datasets & dataloaders", "custom convolutional neural networks"],
            "Week_04": ["cnn optimization, regularization & checkpointing", "transfer learning & backbone benchmarking"],
            "Week_05": ["deep learning semantic segmentation & u-net", "explainable ai & grad-cam"],
            "Week_06": ["image embeddings, clustering & semantic search", "capstone integration & gradio deployment"]
        }
        
        practice_gen.generate(week_distribution, self.context)
        
        # Verify Week_01 numpy_basics files
        numpy_dir = os.path.join(self.output_dir, "exercises", "Week_01", "numpy_basics")
        self.assertTrue(os.path.exists(os.path.join(numpy_dir, "numpy_basics_exercise.py")))
        self.assertTrue(os.path.exists(os.path.join(numpy_dir, "numpy_basics_solution.py")))
        self.assertTrue(os.path.exists(os.path.join(numpy_dir, "numpy_basics_test.py")))
        self.assertTrue(os.path.exists(os.path.join(numpy_dir, "concepts.md")))
        self.assertTrue(os.path.exists(os.path.join(numpy_dir, "resource.md")))


if __name__ == "__main__":
    unittest.main()
