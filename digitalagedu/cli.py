import argparse
import json
from pathlib import Path

from digitalagedu.core.config import load_config
from digitalagedu.core.curriculum_service import CurriculumService
from digitalagedu.core.dataset_scanner import DatasetScanner
from digitalagedu.core.dataset_registry import DATASET_REGISTRY


def main():
    parser = argparse.ArgumentParser(description="DigitalAgEdu Curriculum Engine")

    parser.add_argument("command", choices=["generate"])
    parser.add_argument("config_path", help="Path to YAML config file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--dynamic-weeks", action="store_true")

    args = parser.parse_args()

    if args.command == "generate":
        # Load structured config (Pydantic)
        config = load_config(args.config_path)

        # Scan datasets
        for topic in config.curriculum.topics:
            if topic.dataset_id:
                print(f"Scanning dataset '{topic.dataset_id}' for topic: {topic.name}")
                dataset_entry = DATASET_REGISTRY[topic.dataset_id]
                scanner = DatasetScanner(dataset_entry)
                metadata = scanner.scan()
                topic.dataset_metadata = metadata.model_dump()

        # Build curriculum
        service = CurriculumService(config, dynamic_weeks=args.dynamic_weeks)
        curriculum_output = service.build()

        # Save JSON output
        output_path = Path(args.output).resolve()
        with open(output_path, "w") as f:
            json.dump(curriculum_output, f, indent=4)

        print(f"\nCurriculum successfully saved to: {output_path}\n")


if __name__ == "__main__":
    main()