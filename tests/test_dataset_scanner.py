import pytest
from pathlib import Path
from digitalagedu.core.dataset_scanner import DatasetScanner
from digitalagedu.core.dataset_exceptions import DatasetValidationError, UnsupportedDatasetStructureError

# Sample test folder path (create a small dummy dataset for testing)
TEST_DATASET_DIR = Path("digitalagedu/test/sample_dataset")

def setup_sample_dataset():
    """Create a dummy dataset structure for testing."""
    if not TEST_DATASET_DIR.exists():
        class1 = TEST_DATASET_DIR / "class_a"
        class2 = TEST_DATASET_DIR / "class_b"
        class1.mkdir(parents=True, exist_ok=True)
        class2.mkdir(parents=True, exist_ok=True)
        # Create dummy image files
        for i in range(3):
            (class1 / f"img_{i}.jpg").write_text("dummy")
            (class2 / f"img_{i}.jpg").write_text("dummy")

def teardown_sample_dataset():
    """Remove dummy dataset after tests."""
    if TEST_DATASET_DIR.exists():
        for f in TEST_DATASET_DIR.rglob("*"):
            f.unlink()
        for d in sorted(TEST_DATASET_DIR.rglob("*"), reverse=True):
            if d.is_dir():
                d.rmdir()
        TEST_DATASET_DIR.rmdir()

def test_scan_dataset():
    setup_sample_dataset()
    scanner = DatasetScanner(str(TEST_DATASET_DIR))
    metadata = scanner.scan()

    assert metadata.num_classes == 2
    assert metadata.total_images == 6
    assert metadata.imbalance_ratio == 1.0
    assert set(metadata.class_names) == {"class_a", "class_b"}
    teardown_sample_dataset()

def test_invalid_path():
    scanner = DatasetScanner("nonexistent_path")
    with pytest.raises(DatasetValidationError):
        scanner.validate_structure()

def test_empty_dataset():
    TEST_DATASET_DIR.mkdir(exist_ok=True)
    scanner = DatasetScanner(str(TEST_DATASET_DIR))
    with pytest.raises(UnsupportedDatasetStructureError):
        scanner.validate_structure()
    TEST_DATASET_DIR.rmdir()
