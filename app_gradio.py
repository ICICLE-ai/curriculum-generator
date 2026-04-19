import sys
import os

# 1. Modify path IMMEDIATELY before other imports
sys.path.append("/fs/ess/PAS2699/mhole/curriculum_generator/Code")

import gradio as gr
import json
import traceback

# 2. These must be importable without error for the API to register
try:
    from digitalagedu.core.curriculum_service import CurriculumService
    from run_pipeline import run_pipeline_entry
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    # Define dummy functions so the UI at least launches for debugging
    def run_pipeline_entry(*args, **kwargs): return "Import Error", None
    def CurriculumService(*args, **kwargs): return None

DATASET_MAP = {
    "Soybean Disease Detection": "/fs/ess/PAS2699/mhole/datasets/soybean_disease",
    "Corn Disease Detection": "/fs/ess/PAS2699/mhole/datasets/corn_disease",
    "Corn Residue Cover Analysis": "/fs/ess/PAS2699/mhole/datasets/corn_residue",
    "Soil Aggregate Size Analysis": "/fs/ess/PAS2699/mhole/datasets/soil_aggregate"
}

def generate_curriculum_ui(dataset_name, subject, grade, instructor):
    try:
        # Minimal Mock classes for service requirement
        class Topic:
            def __init__(self, name):
                self.name = name
                self.description = ""
                self.project = ""
                self.dataset_metadata = {"num_classes": 2, "total_images": 1000, "difficulty_level": "intermediate"}
        class Curriculum:
            def __init__(self):
                self.subject = subject
                self.grade = grade
                self.topics = [Topic(dataset_name)]
        class Config:
            def __init__(self): self.curriculum = Curriculum()

        service = CurriculumService(Config())
        result = service.build()

        os.makedirs("./outputs", exist_ok=True)
        output_path = f"./outputs/{dataset_name.replace(' ', '_')}_curriculum.json"

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        return output_path
    except Exception:
        return traceback.format_exc()

def run_full_pipeline(dataset, batch_choice, task, custom_val, out_dir):
    try:
        dataset_root = DATASET_MAP[dataset]
        # Resolve batch size logic
        final_count = int(custom_val) if batch_choice == "Custom" else int(batch_choice)

        status, img_path = run_pipeline_entry(
            dataset_root=dataset_root,
            max_images=final_count,
            task_type=task,
            output_dir=out_dir
        )
        return status, img_path
    except Exception:
        return traceback.format_exc(), None

# -----------------------------
# UI
# -----------------------------
with gr.Blocks(title="DigitalAgEdu") as demo:
    gr.Markdown("# DigitalAgEdu\nLearn AI through real agricultural datasets")

    with gr.Tab("Curriculum Builder"):
        with gr.Column():
            dataset_curr = gr.Dropdown(list(DATASET_MAP.keys()), label="Select Dataset")
            subject = gr.Textbox(value="Digital Agriculture", label="Subject")
            grade = gr.Number(value=10, label="Grade")
            instructor = gr.Textbox(label="Instructor")
            btn_curr = gr.Button("Generate Curriculum", variant="primary")
            out_file = gr.File(label="Output JSON")

        btn_curr.click(generate_curriculum_ui, [dataset_curr, subject, grade, instructor], out_file)

    with gr.Tab("Pipeline Runner"):
        with gr.Row():
            dataset_pipe = gr.Dropdown(list(DATASET_MAP.keys()), label="Dataset")
            task_type = gr.Radio(["disease_detection", "soil_analysis", "residue_analysis"], value="soil_analysis", label="Task")
        
        with gr.Row():
            batch_choice = gr.Radio(["1", "5", "10", "Custom"], value="5", label="Batch Size")
            custom_batch = gr.Number(value=1, label="Custom Value")
        
        output_dir = gr.Textbox(value="./AI_Pipeline_Results", label="Output Directory")
        btn_run = gr.Button("Run Pipeline", variant="primary")

        out_status = gr.Textbox(label="Status")
        # CRITICAL: Added type="filepath" because your function returns a string path
        out_image = gr.Image(label="Segmented Output", type="filepath")

        btn_run.click(
            run_full_pipeline,
            [dataset_pipe, batch_choice, task_type, custom_batch, output_dir],
            [out_status, out_image]
        )

if __name__ == "__main__":
    # Setting show_api=False prevents Gradio from running the 
    # schema generation logic that is triggering the TypeError.
    demo.launch(
        share=True, 
        debug=True, 
        show_api=False
    )