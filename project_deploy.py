# coding: utf-8

import requests
import rich_click as click
import git
import os

from snakedeploy.deploy import deploy
from rich.console import Console
from pathlib import Path

# List of available pipelines
pipelines: tuple[str] = (
    "fair_genome_indexer",
    "fair_fastqc_multiqc",
    "fair_rnaseq_salmon_quant",
    "fair_bowtie2_mapping",
    "fair_star_mapping",
)


@click.command(context_settings={"show_default": True})
@click.argument("pipeline", type=click.Choice(pipelines), required=True)
@click.option("-t", "--tag", type=str, default="latest", help="Github tag version")
@click.option(
    "-w",
    "--workdir",
    type=click.Path(),
    default=os.getcwd(),
    help="Path to working directory",
)
@click.option(
    "-f", "--force", is_flag=True, help="Force pipeline over-writing", default=False
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Raise verbosity level", default=False
)
@click.help_option("--help", "-h")
def deploy_pipeline(
    pipeline: str,
    tag: str = "latest",
    workdir: str | Path = os.getcwd(),
    force: bool = False,
    verbose: bool = False,
) -> None:
    """Deploy a snakemake pipeline"""
    console = Console()
    if verbose:
        console.print(f"Deploying {pipeline}...", style="green")

    # Build pipeline address
    git_address: str = f"https://github.com/tdayris/{pipeline}"
    name: str = pipeline.capitalize()

    # Get latest tag through blob name
    # https://github.com/gitpython-developers/GitPython/issues/1071
    if tag == "latest":
        g = git.cmd.Git()
        blob: str = g.ls_remote(git_address, sort="-v:refname", tags=True)
        tag = blob.split("\n")[0].split("/")[-1]
        if verbose:
            console.print(f"Pipeline version is: {tag}", style="green")

    # Build IO directories
    if isinstance(workdir, str):
        workdir = Path(workdir)

    config_dir: Path = workdir / "config"
    workflow_dir: Path = workdir / "workflow"

    # Deploy pipelines
    if force or (not (config_dir.exists() or workflow_dir.exists())):
        deploy(
            source_url=git_address,
            name=name,
            tag=tag,
            branch=None,
            dest_path=workdir,
            force=force,
        )
    elif verbose:
        console.print(
            f":warning: warning: A pipeline has already been deployed at `{workdir.resolve()}`",
            style="dark_orange",
        )

    if verbose:
        console.print(":ballot_box_with_check: Pipeline deployed", style="green")

if __name__ == "__main__":
    deploy_pipeline()
