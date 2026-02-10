import typer
from digitalagedu.core.config import load_config

app = typer.Typer()

@app.command("generate")
def generate_curriculum(config: str = typer.Argument(..., help="Path to YAML/JSON config file")):
    """
    Generate curriculum from a YAML/JSON config file.
    """
    cfg = load_config(config)
    typer.echo(f"Loaded curriculum for grade {cfg.curriculum.grade}:")
    for i, topic in enumerate(cfg.curriculum.topics, 1):
        typer.echo(f"{i}. {topic.name} - {topic.project}")
    # typer.echo(f"Generating curriculum from {config}")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    DigitalAgEdu: Digital agriculture curriculum generation engine for K-12 students.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("Use --help to see available commands")