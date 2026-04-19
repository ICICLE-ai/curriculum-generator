"""
WEEK 2 STARTER CODE
Dataset Explorer
"""

import os
from PIL import Image
import matplotlib.pyplot as plt

# TODO: Change this to your dataset folder
DATASET_PATH = "your_dataset_folder_here"


def get_class_names(dataset_path):
    """
    Return a list of folder names inside dataset_path.
    """
    # TODO: Write code here
    pass


def count_images_in_class(dataset_path, class_name):
    """
    Count how many image files are inside one class folder.
    """
    # TODO: Write code here
    pass


def show_sample_image(dataset_path, class_name):
    """
    Show one sample image from the class.
    """
    # TODO: Write code here
    pass


if __name__ == "__main__":

    classes = get_class_names(DATASET_PATH)

    print("\n Classes Found:")
    print(classes)

    print("\n Image Count Per Class:")

    for cls in classes:
        count = count_images_in_class(DATASET_PATH, cls)
        print(f"{cls}: {count} images")

    print("\n Showing Sample Images...")
    for cls in classes:
        show_sample_image(DATASET_PATH, cls)