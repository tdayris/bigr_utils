# coding: utf-8

import os
import rich_click as click
import subprocess
import sys

from pathlib import Path
from snakemake.shell import shell
from rich.console import Console

@click.command(context_settings={"show_default": True})
@click.option("--tag", type=str, default="latest", help="Github tag version")
@click.option(
    "--workdir",
    type=click.Path(),
    default=os.getcwd(),
    help="Path to workind directory",
)
@click.option(
    "-p",
    "--profile",
    type=click.Path(),
    default="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/profiles/slurm-web-8/",
    help="Path to Snakemake profile",
)
@click.option(
    "--snakemake_cache",
    type=click.Path(),
    default="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/snakemake_cache",
    help="Path to snakemake cache dir to avoid index over-writing",
)
@click.option(
    "--conda_cache",
    type=click.Path(),
    default="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/conda_cache",
    help="Path to conda cache dir to avoid repetitive package downloads",
)
@click.option(
    "--conda_env",
    type=click.Path(),
    default="/mnt/beegfs/userdata/t_dayris/anaconda/envs/snakemake",
    help="Path to conda environment",
)
@click.option(
    "-m", "--mem", type=str, default="1G", help="Amount of memory for snakemake"
)
@click.option(
    "-t",
    "--time",
    type=str,
    default="0-05:59:59",
    help="Amount of time required for your pipeline D-H:M:S",
)
@click.option(
    "-f", "--force", is_flag=True, default=False, help="Force pipeline over-writing"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Increase verbosity level"
)
@click.help_option("-h", "--help")
def deploy_fair_fastqc_multiqc(
    tag: str = "latest",
    workdir: str | Path = os.getcwd(),
    profile: (
        str | Path
    ) = "/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/profiles/slurm-web-8/",
    snakemake_cache: (
        str | Path
    ) = "/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/snakemake_cache",
    conda_cache: (
        str | Path
    ) = "/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/conda_cache",
    conda_env: (
        str | Path
    ) = "/mnt/beegfs/userdata/t_dayris/anaconda/envs/snakemake_v8.11.6",
    force: bool = False,
    verbose: bool = False,
    mem: str = "1G",
    time: str = "5:59:59",
) -> None:
    """
    Deploy fair fastqc multiqc pipeline from https://github.com/tdayris/fair_fastqc_multiqc
    """
    console = Console()

    # Define locals
    script_path: Path = Path(__file__)
    script_dir: Path = script_path.parent
    pipeline: str = "fair_fastqc_multiqc"
    extra: str = ""
    if verbose is True:
        extra += "--verbose "
    if force is True:
        force += "--force "

    # Build IO paths
    if isinstance(workdir, str):
        workdir = Path(workdir)

    genomes_csv: Path = workdir / "config" / "genomes.csv"
    samples_csv: Path = workdir / "config" / "samples.csv"
    config_yaml: Path = workdir / "config" / "config.yaml"
    workflow_smk: Path = workdir / "workflow" / "Snakefile"
    sbatch_sh: Path = workdir / "scripts" / "sbatch.sh"

    # Running subscripts
    # 1. Deploying snakemake pipeline
    try:
        shell(
            'python3 '
            f'"{script_dir}/project_deploy.py" '
            f'"{pipeline}" '
            f'--tag "{tag}" '
            f'--workdir "{workdir}" '
            f'{extra} '
        )
    
        # 2. Creating configuration file
        shell(
            'python3 '
            f'"{script_dir}/project_config.py" '
            f'--samples "{samples_csv}" '
            f'--genomes "{genomes_csv}" '
            f'--output "{config_yaml}" '
            f'--workflow "{workflow_smk}" '
            f'{extra}'
        )

        # 3. Creating genomes file
        shell(
            'python3 '
            f'"{script_dir}/project_genomes.py" '
            f'--output "{genomes_csv}" '
            f'{extra} '
        )

        # 4. Creating sbatch script
        shell(
            'python3 '
            f'"{script_dir}/project_sbatch.py" '
            f'--workdir "{workdir}" '
            f'--config "{config_yaml}" '
            f'--output "{sbatch_sh}" '
            f'--profile "{profile}" '
            f'--snakemake_cache "{snakemake_cache}" '
            f'--conda_cache "{conda_cache}" '
            f'--conda_env "{conda_env}" '
            f'--mem "{mem}" '
            f'--time "{time}" '
            f'{extra} '
        )
    except subprocess.CalledProcessError:
        console.print_exception(show_locals=False)
        sys.exit(1)


    # Post deployment utilities
    # Giving user a hint of what's available
    if verbose:
        shell(
            'python3 '
            f'{script_dir}/project_tree.py '
            f'--directory {workdir} '
        )
    
    console.print(f"Use '{script_dir}/project_samples.py' to get your file paths from iRODS.")

if __name__ == "__main__":
    deploy_fair_fastqc_multiqc()
