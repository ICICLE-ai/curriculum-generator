from pathlib import Path


class FileWriter:
    def write(self, content: str, output_path: str):
        path = Path(output_path)
        # Ensure output directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file with encoding
        path.write_text(content, encoding="utf-8")

        print(f"Generated file at {path.resolve()}")