import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from digitalagedu.core.llm.presenton_client import PresentonClient, PresentonGenerationError
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.context import build_presenton_payload


class TestPresentonIntegration(unittest.TestCase):

    def setUp(self):
        self.client = PresentonClient(endpoint="http://localhost:5001", timeout=30.0)
        self.module = Module(
            id="dinov2_adaptation",
            title="Vision Transformer Feature Extraction",
            week=1,
            context="Dermatoscopic skin lesion classification using foundation ViT backbones",
            difficulty="intermediate"
        )
        self.problem_formulation = ProblemStatementSchema(
            title="Dermatoscopic Malignancy Classifier",
            domain_context="ISIC Skin Lesion benchmark with 2 classes (benign vs malignant).",
            problem_statement="Mitigate false negative diagnostics by training a custom classifier head on top of frozen DINOv2 embeddings.",
            learning_objectives=[
                "Understand self-supervised Vision Transformer patch embeddings",
                "Implement classifier head swapping with frozen backbones in PyTorch",
                "Evaluate false negative trade-offs on imbalanced clinical datasets"
            ],
            target_input_shape="[4, 3, 224, 224]",
            target_output_shape="[4, 2]",
            suggested_focus="Frozen DINOv2 Feature Extractor + Linear Probing",
            markdown_overview="# Overview\n\nClinical dermatology diagnostic AI."
        )
        self.telemetry = {
            "run_summary": {
                "total_images": 2637,
                "overall_accuracy": 86.4
            },
            "class_mapping": {
                "0": "benign",
                "1": "malignant"
            },
            "contrastive_samples": {
                "top_success": {
                    "image_path": "benign/ISIC_0000023.jpg",
                    "ground_truth": "benign",
                    "confidence": 0.99
                },
                "hard_failure": {
                    "image_path": "malignant/ISIC_0000142.jpg",
                    "ground_truth": "malignant",
                    "predicted_class": "benign"
                }
            }
        }
        self.solution_code = (
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class LesionClassifier(nn.Module):\n"
            "    def __init__(self, num_classes=2):\n"
            "        super().__init__()\n"
            "        self.backbone = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')\n"
            "        for param in self.backbone.parameters():\n"
            "            param.requires_grad = False\n"
            "        self.head = nn.Linear(384, num_classes)\n\n"
            "    def forward(self, x):\n"
            "        feats = self.backbone(x)\n"
            "        return self.head(feats)\n"
        )

    def test_build_presenton_payload_rich_grounding(self):
        """Verify build_presenton_payload integrates domain, code, and telemetry context."""
        payload = build_presenton_payload(
            module=self.module,
            problem_formulation=self.problem_formulation,
            solution_code=self.solution_code,
            telemetry=self.telemetry
        )

        self.assertIn("content", payload)
        self.assertIn("slides_markdown", payload)
        self.assertIn("instructions", payload)
        self.assertEqual(payload["tone"], "educational")

        content = payload["content"]
        # Verify domain & problem statement injection
        self.assertIn("ISIC Skin Lesion benchmark", content)
        self.assertIn("Mitigate false negative diagnostics", content)
        self.assertIn("[4, 3, 224, 224]", content)
        self.assertIn("[4, 2]", content)

        # Verify telemetry & contrastive case studies injection
        self.assertIn("2637 authentic images", content)
        self.assertIn("86.4%", content)
        self.assertIn("ISIC_0000023.jpg", content)
        self.assertIn("ISIC_0000142.jpg", content)

        # Verify slides_markdown structure
        slides = payload["slides_markdown"]
        self.assertGreaterEqual(len(slides), 4)
        
        # Verify code snippet in slide markdown
        code_slide = any("```python" in s and "LesionClassifier" in s for s in slides)
        self.assertTrue(code_slide, "Expected PyTorch code snippet to be embedded in slides_markdown")

        # Verify telemetry contrastive slide
        telemetry_slide = any("ISIC_0000142.jpg" in s for s in slides)
        self.assertTrue(telemetry_slide, "Expected diagnostic telemetry case study in slides_markdown")

    @patch("requests.get")
    def test_check_health(self, mock_get):
        """Verify health check logic."""
        mock_get.return_value.status_code = 200
        self.assertTrue(self.client.check_health())

        mock_get.side_effect = Exception("Connection refused")
        self.assertFalse(self.client.check_health())

    @patch("requests.post")
    @patch("requests.get")
    def test_generate_presentation_success(self, mock_get, mock_post):
        """Verify headless synchronous generation and PPTX streaming."""
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "presentation_id": "test-uuid-1234",
            "path": "/app_data/exports/test-uuid-1234.pptx",
            "edit_path": "/edit/test-uuid-1234"
        }

        mock_get.return_value.ok = True
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"PK\x03\x04MockPowerPointBinaryBytes"

        with tempfile.TemporaryDirectory() as tmpdir:
            out_pptx = os.path.join(tmpdir, "test_presentation.pptx")
            res_path = self.client.generate_presentation(
                content="Domain lesson content",
                output_path=out_pptx,
                slides_markdown=["# Slide 1", "# Slide 2"],
                n_slides=2
            )

            self.assertEqual(res_path, out_pptx)
            self.assertTrue(os.path.exists(out_pptx))
            with open(out_pptx, "rb") as f:
                saved_bytes = f.read()
            self.assertEqual(saved_bytes, b"PK\x03\x04MockPowerPointBinaryBytes")

            # Verify POST request payload against Presenton API schema
            call_args, call_kwargs = mock_post.call_args
            self.assertEqual(call_args[0], "http://localhost:5001/api/v1/ppt/presentation/generate")
            sent_json = call_kwargs["json"]
            self.assertEqual(sent_json["content"], "Domain lesson content")
            self.assertEqual(sent_json["export_as"], "pptx")
            self.assertEqual(sent_json["tone"], "educational")

    @patch("requests.post")
    def test_generate_presentation_error_handling(self, mock_post):
        """Verify error is raised when Presenton API returns failure."""
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Presenton layout error"

        with tempfile.TemporaryDirectory() as tmpdir:
            out_pptx = os.path.join(tmpdir, "test_presentation.pptx")
            with self.assertRaises(PresentonGenerationError) as ctx:
                self.client.generate_presentation(
                    content="Faulty content",
                    output_path=out_pptx
                )
            self.assertIn("Presenton API generation failed with status 500", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
