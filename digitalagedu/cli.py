import typer
from digitalagedu.core.config import load_config
from digitalagedu.core.orchestrator import CurriculumEngine

app = typer.Typer()

@app.command("generate")
def generate_curriculum(config: str = typer.Argument(..., help="Path to YAML/JSON config file")):
    """
    Generate curriculum from a YAML/JSON config file.
    """
    # Initialize engine
    engine = CurriculumEngine(config)

    # Run engine: this now integrates dataset metadata internally
    lesson_data = engine.run()

    # Print summary of datasets scanned
    for topic in lesson_data["topics"]:
        if "dataset_metadata" in topic:
            typer.echo(f"Dataset for topic: {topic['name']}")
            md = topic["dataset_metadata"]
            typer.echo(f"  Classes: {md['num_classes']}, Total images: {md['total_images']}")
            typer.echo(f"  Imbalance ratio: {md['imbalance_ratio']}, Size: {md['size_category']}")
            typer.echo(f"  Difficulty: {md['difficulty_level']}")
            typer.echo(f"  Suggested metrics: {', '.join(md['suggested_metrics'])}")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    DigitalAgEdu: Digital agriculture curriculum generation engine for K-12 students.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("Use --help to see available commands")
