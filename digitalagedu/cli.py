import typer
from digitalagedu.core.orchestrator import CurriculumEngine

app = typer.Typer()


@app.command("generate")
def generate_curriculum(
    config: str = typer.Argument(..., help="Path to YAML/JSON config file")
):
    """
    Generate curriculum from a YAML/JSON config file.
    """
    engine = CurriculumEngine(config)
    engine.run()

    typer.echo("Curriculum generated successfully!")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    DigitalAgEdu: Digital agriculture curriculum generation engine for K-12 students.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("Use --help to see available commands")
