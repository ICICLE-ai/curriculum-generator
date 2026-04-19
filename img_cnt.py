import os

# Supported image extensions
IMAGE_EXTENSIONS = {
    ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".svg",
    ".bmp", ".gif", ".webp"
}

def count_images(root_folder):
    total_count = 0

    for dirpath, dirnames, filenames in os.walk(root_folder):
        for file in filenames:
            _, ext = os.path.splitext(file)
            if ext.lower() in IMAGE_EXTENSIONS:
                total_count += 1

    return total_count


if __name__ == "__main__":
    folder_path = input("Enter folder path: ").strip()

    if not os.path.exists(folder_path):
        print("Invalid folder path.")
    else:
        count = count_images(folder_path)
        print(f"Total images found: {count}")