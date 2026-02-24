DATASET_REGISTRY = {
    "soybean_disease": {
        "path": "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans",
        "task_type": "classification"
    },
    "corn_disease": {
        "path": "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Corn/Corn",
        "task_type": "classification"
    },
    "corn_residue": {
        "path": "/fs/ess/PAS2699/crdean95",
        "task_type": "segmentation",
        "allowed_subfolders": [
            "GP Tillage Test 1",
            "GP Tillage Test 2 Snip",
            "GP Tillage Test 3 Snip",
            "GP Tillage Test 4"
        ]
    },
    "soil_aggregate": {
        "path": "/fs/ess/PAS2699/crdean95",
        "task_type": "measurement",
        "allowed_subfolders": [
            "GP Tillage Test 1",
            "GP Tillage Test 2 Snip",
            "GP Tillage Test 3 Snip",
            "GP Tillage Test 4"
        ]
    }
}