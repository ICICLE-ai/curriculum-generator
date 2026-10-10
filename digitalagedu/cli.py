import argparse
import json
from pathlib import Path

from digitalagedu.core import load_config, CurriculumService, DatasetScanner


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

        # Scan dataset dynamically
        scanner = DatasetScanner(config.dataset.root_path)
        metadata = scanner.scan()
        for topic in config.curriculum.topics:
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