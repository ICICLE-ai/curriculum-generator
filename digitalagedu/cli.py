import argparse
import json
from pathlib import Path

from digitalagedu.core.config import load_config
from digitalagedu.core.curriculum_service import CurriculumService


def main():
    parser = argparse.ArgumentParser(description="DigitalAgEdu Curriculum Engine")
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("config_path", help="Path to YAML config file")
    parser.add_argument(
        "--output",
        default="generated_curriculum.json",
        help="Output file name (default: generated_curriculum.json)",
    )

    args = parser.parse_args()

    if args.command == "generate":
        # Load & validate config
        config = load_config(args.config_path)

        # Build curriculum
        service = CurriculumService(config)
        curriculum_output = service.build()

        # Convert metadata objects to serializable dict
        def serialize(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        # Save to file
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(curriculum_output, f, indent=4, default=serialize)

        print(f"Curriculum successfully saved to: {output_path}")


if __name__ == "__main__":
    main()