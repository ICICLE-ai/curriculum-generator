import os
import sys
import shutil

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.practice_generator import PracticeGenerator
from digitalagedu.core.config import load_config

def main():
    print("[INFO] Setting up testing directory and environment...")
    
    # Create test datasets folders with dummy images so that dataset loading and cnn tests don't crash
    dataset_root = "./test_datasets"
    classes = ["benign", "malignant"]
    for cls in classes:
        cls_dir = os.path.join(dataset_root, cls)
        os.makedirs(cls_dir, exist_ok=True)
        # Create tiny dummy JPEGs
        from PIL import Image
        for i in range(5):
            img = Image.new("RGB", (10, 10), color="red")
            img.save(os.path.join(cls_dir, f"img_{i}.jpg"))
            
    # Mock results.csv
    import pandas as pd
    csv_path = "./outputs/results.csv"
    os.makedirs("./outputs", exist_ok=True)
    df_data = {
        'image_path': [os.path.join(dataset_root, "benign", "img_0.jpg")] * 15,
        'ground_truth': ["benign"] * 15,
        'predicted_class': ["benign"] * 15,
        'confidence': [0.95] * 15
    }
    pd.DataFrame(df_data).to_csv(csv_path, index=False)
    
    # Set up generator
    templates_dir = "./digitalagedu/templates"
    output_dir = "./outputs/test_run"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Dummy config
    class DummyConfig:
        def __init__(self):
            class Exec:
                image_size = 224
            class Data:
                train_split = 0.8
                root_path = dataset_root
            self.execution = Exec()
            self.dataset = Data()
            
    config = DummyConfig()
    
    generator = PracticeGenerator(
        templates_dir=templates_dir,
        output_dir=output_dir,
        config=config
    )
    
    # All 13 weekly exercises to verify
    week_dist = {
        "Week_01": ["numpy basics array calculations and Z-score normalization"],
        "Week_02": ["pandas & matplotlib data analysis and plotting"],
        "Week_03_04": ["deep learning foundations classifier"],
        "Week_05": ["interactive image segmentation floodfill"],
        "Week_06_07": ["pytorch datasets & dataloaders loading batches"],
        "Week_08_09": ["custom convolutional neural networks feature maps"],
        "Week_10_11": ["tune cnn optimization, regularization & checkpointing"],
        "Week_12_13": ["perform transfer learning & backbone benchmarking"],
        "Week_14_15": ["build a deep learning semantic segmentation & u-net"],
        "Week_16_17": ["explainable ai & grad-cam attention maps"],
        "Week_18_19": ["image embeddings, clustering & semantic search"],
        "Week_20_21": ["vision-language models explanations"],
        "Week_22_23_24": ["capstone integration & gradio deployment app"]
    }
    
    context = {
        "subject": "Intro to Medical AI",
        "grade": 10,
        "class_mapping": classes,
        "image_size": 224,
        "train_split": 0.8,
        "dataset_root": dataset_root,
        "sample_image_path": os.path.join(dataset_root, "benign", "img_0.jpg"),
        "sample_mask_path": os.path.join(dataset_root, "benign", "img_0.jpg") # use image itself as mask for simplicity
    }
    
    # Run the generator. This renders, compiles, and headlessly verifies all 13 templates.
    print("[INFO] Initiating template rendering and verification...")
    generator.generate(week_dist, context)
    
    print("[INFO] Cleaning up test mock dataset and CSV...")
    if os.path.exists(dataset_root):
        shutil.rmtree(dataset_root, ignore_errors=True)
    if os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except Exception:
            pass

if __name__ == "__main__":
    main()
