import typer
from digitalagedu.core.config import load_config
from digitalagedu.core.orchestrator import CurriculumEngine
from digitalagedu.core.dataset_scanner import DatasetScanner

app = typer.Typer()

@app.command("generate")
def generate_curriculum(config: str = typer.Argument(..., help="Path to YAML/JSON config file")):
    """
    Generate curriculum from a YAML/JSON config file.
    """
    # Load config
    engine = CurriculumEngine(config)

    # Validate dataset for each topic if dataset_path provided
    for topic in engine.config.curriculum.topics:
        if hasattr(topic, "dataset_path") and topic.dataset_path:
            typer.echo(f"Scanning dataset for topic: {topic.name}")
            scanner = DatasetScanner(topic.dataset_path)
            metadata = scanner.scan()
            typer.echo(metadata.summary())

    # Run engine to generate lesson plan
    engine.run()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    DigitalAgEdu: Digital agriculture curriculum generation engine for K-12 students.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("Use --help to see available commands")
