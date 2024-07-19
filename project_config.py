# coding: utf-8

import rich_click as click
import os
import yaml
import sys

from rich.console import Console
from pathlib import Path


def check_path(path: str) -> None:
    """Check if path exists"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not file {path}")


@click.command(context_settings={"show_default": True})
@click.option(
    "-s",
    "--samples",
    type=click.Path(),
    default=f"{os.getcwd()}/config/samples.csv",
    help="Path to `samples.csv` file",
)
@click.option(
    "-g",
    "--genomes",
    type=click.Path(),
    default=f"{os.getcwd()}/config/genomes.csv",
    help="Path to `genomes.csv` file",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=f"{os.getcwd()}/config/config.yaml",
    help="Path to output file",
)
@click.option(
    "-w",
    "--workflow",
    type=click.Path(),
    default=f"{os.getcwd()}/workflow/Snakefile",
    help="Path to the snakefile",
)
@click.option(
    "-s",
    "--fastq_screen_config",
    type=click.Path(),
    default="/mnt/beegfs/database/bioinfo/Index_DB/Fastq_Screen/0.14.0/fastq_screen.conf",
    help="Path to FastqScreen database configuration file",
)
@click.option(
    "-p",
    "--params",
    help="A 'key=value' parameter",
    multiple=True,
    default=[""],
)
@click.option("-f", "--force", is_flag=True, help="Force over-writing", default=False)
@click.option(
    "-v", "--verbose", is_flag=True, help="Raise verbosity level", default=False
)
@click.help_option("--help", "-h")
def create_config(
    samples: Path | str = f"{os.getcwd()}/config/samples.csv",
    genomes: Path | str = f"{os.getcwd()}/config/genomes.csv",
    output: Path | str = f"{os.getcwd()}/config/config.yaml",
    workflow: Path | str = f"{os.getcwd()}/workflow/Snakefile",
    fastq_screen_config: (
        Path | str
    ) = "/mnt/beegfs/database/bioinfo/Index_DB/Fastq_Screen/0.14.0/fastq_screen.conf",
    params=[""],
    force: bool = False,
    verbose: bool = False,
) -> None:
    """Create a configuration file suitable for the pipelines"""
    console = Console()

    if verbose:
        console.print(f"Configuring pipeline...", style="green")

    pipeline: str = "Unknown"
    tag: str = "Unknown"

    # Check file path
    for file_path in (samples, genomes, workflow):
        try:
            check_path(file_path)
        except FileNotFoundError:
            console.print_exception(show_locals=True)
            sys.exit(1)

    # Search pipeline version and name
    with open(workflow, "r") as snakefile_stream:
        for line in snakefile_stream:
            if line.startswith("        github("):
                content: list[str] = line.split('"')
                pipeline = content[1].split("/")[-1]
                tag = content[-2]
                break
        else:
            console.print(
                f":warning: warning: Could not find pipeline version",
                style="dark_orange",
            )

    # Content of the fonciguration file
    config: dict[str, dict[str, str] | str] = {
        "genomes": genomes,
        "samples": samples,
        "pipeline": {
            "name": pipeline,
            "tag": tag,
        },
        "params": {
            "fair_fastqc_multiqc_fastq_screen_config": fastq_screen_config,
        },
    }

    for parameter in params:
        if "=" in parameter:
            key, value = parameter.split("=")
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            config["params"][key] = value

    # Save configuration
    if force or (not Path(output).exists):
        with open(output, "w") as yaml_stream:
            console.print(config, style="green")
            yaml.dump(config, yaml_stream, default_flow_style=False)

    if verbose:
        console.print(
            ":ballot_box_with_check: Configuration file available", style="green"
        )


if __name__ == "__main__":
    create_config()
