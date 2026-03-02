from digitalagedu.core.dataset_scanner import DatasetScanner
from digitalagedu.core.dataset_registry import DATASET_REGISTRY

if __name__ == "__main__":
    dataset_entry = DATASET_REGISTRY["soybean_disease"]

    scanner = DatasetScanner(dataset_entry)
    metadata = scanner.scan()

    print("\nFull Metadata Object:")
    print(metadata.model_dump())