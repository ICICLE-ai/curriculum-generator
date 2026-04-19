import os
from PIL import Image
import matplotlib.pyplot as plt


DATASET_PATH = "your_dataset_folder_here"


def get_class_names(dataset_path):
    return [
        folder for folder in os.listdir(dataset_path)
        if os.path.isdir(os.path.join(dataset_path, folder))
    ]


def count_images_in_class(dataset_path, class_name):
    class_path = os.path.join(dataset_path, class_name)

    image_files = [
        f for f in os.listdir(class_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    return len(image_files)


def show_sample_image(dataset_path, class_name):
    class_path = os.path.join(dataset_path, class_name)

    image_files = [
        f for f in os.listdir(class_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if len(image_files) == 0:
        return

    img_path = os.path.join(class_path, image_files[0])
    img = Image.open(img_path)

    plt.imshow(img)
    plt.title(class_name)
    plt.axis("off")
    plt.show()


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