from pathlib import Path

NUM_WEEKS = 16  # maximum weeks
BASE_FOLDER = Path("curriculum_resources")

# -------------------------------
# Prerequisites folder
# -------------------------------
python_basics_folder = BASE_FOLDER / "python_basics"
python_basics_folder.mkdir(parents=True, exist_ok=True)
(python_basics_folder / "README.md").write_text(
    "# Python Basics Prerequisites\n\n"
    "Recommended resources:\n"
    "- [Official Python Documentation](https://docs.python.org/3/tutorial/)\n"
    "- [W3Schools Python Tutorial](https://www.w3schools.com/python/)\n"
    "- [Python for Everybody - YouTube](https://www.youtube.com/playlist?list=PLlAnjvJ5U1WhYfYtN0N6krH1k0o10cTzo)\n"
)

# -------------------------------
# Create weekly folders
# -------------------------------
for week in range(1, NUM_WEEKS + 1):
    week_folder = BASE_FOLDER / f"week_{week:02d}"
    week_folder.mkdir(parents=True, exist_ok=True)

    # Starter code placeholder
    starter_code = week_folder / "starter_code.ipynb"
    starter_code.write_text(f"# Week {week:02d} Starter Code\n\n# TODO: Add starter notebook content here")

    # Solution code placeholder
    solution_code = week_folder / "solution.ipynb"
    solution_code.write_text(f"# Week {week:02d} Solution Code\n\n# TODO: Add solution notebook content here")

    # References placeholder
    references = week_folder / "references.md"
    references.write_text(f"# Week {week:02d} References\n\n# TODO: Add reading links, articles, videos, or docs here")

print(f"Curriculum resources folder created at: {BASE_FOLDER.resolve()}")