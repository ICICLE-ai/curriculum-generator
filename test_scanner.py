from digitalagedu.core.dataset_scanner import DatasetScanner

dataset_path = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Corn/Corn"

scanner = DatasetScanner(dataset_path)
metadata = scanner.scan()

print(metadata.summary())
print("\nFull Metadata Object:")
print(metadata.model_dump())

# dataset_path = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans"
