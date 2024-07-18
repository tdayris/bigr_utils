# coding: utf-8

import rich_click as click
import os
import sys
import yaml

from pathlib import Path
from rich.console import Console


def time_to_minutes(time: str) -> int:
    """Convert several time formats into minutes"""
    if "-" in time:
        # Then there are days
        day, hours = time.split("-")
        hours = time_to_minutes(hours)
        return int(day) * 1440 + hours

    if ":" in time:
        # Then there are hours
        hours, minutes, seconds = time.split(":")
        return int(round((int(hours) * 60) + int(minutes) + (int(seconds) / 60)))

    return int(round(time))


def minutes_to_human_readable_time(minutes: int) -> str:
    """Return a human readable time"""
    days: int = minutes // 1440
    minutes %= 1440
    hours: int = minutes // 60
    minutes %= 60
    return f"{days}-{hours}:{minutes}:00"


def select_queue(minutes: int) -> str:
    """Select the best queue according to requirements"""
    if minutes <= 360:
        return "shortq"

    if minutes <= 1440:
        return "mediumq"

    if minutes <= 10080:
        return "longq"

    if minutes <= 86400:
        return "verylongq"

    # Handle wrong user time reservation
    time: str = minutes_to_human_readable_time(minutes)
    raise ValueError(f"Too much time requested: {time}")


@click.command(context_settings={"show_default": True})
@click.option(
    "-w",
    "--workdir",
    type=click.Path(),
    default=os.getcwd(),
    help="Path to working directory",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(),
    default=f"{os.getcwd()}/config/config.yaml",
    help="Path to pipeline configuration file",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=f"{os.getcwd()}/scripts/sbatch.sh",
    help="Path to launcher script",
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
    default="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/shared_install/snakemake/",
    help="Path to conda environment",
)
@click.option(
    "-f", "--force", is_flag=True, default=False, help="Force script over-writing."
)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Increase verbosity")
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
@click.help_option("-h", "--help")
def sbatch_creator(
    workdir: str | Path = os.getcwd(),
    config: str | Path = f"{os.getcwd()}/config/config.yaml",
    output: str | Path = f"{os.getcwd()}/scripts/sbatch.sh",
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
    """Create a sbatch launcher script"""
    console = Console()

    if verbose:
        console.print("Building sbatch script...", style="green")

    # Create IO directories if missing
    if isinstance(conda_env, str):
        conda_env = Path(conda_env)
    conda_sh = conda_env / "etc/profile.d/conda.sh"
    mamba_sh = conda_env / "etc/profile.d/mamba.sh"

    if isinstance(workdir, str):
        workdir = Path(workdir)

    log_dir: Path = workdir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir: Path = workdir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    scripts_dir: Path = workdir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Define Flamingo queue
    try:
        minutes: int = time_to_minutes(time)
        queue: str = select_queue(minutes)
        time: str = minutes_to_human_readable_time(minutes)
    except ValueError:
        console.print_exception(show_locals=True)
        sys.exit(1)

    # Define project name and description
    with open(config, "r") as config_yaml_stream:
        config_content: dict[str, str | dict[str, str]] = yaml.safe_load(
            config_yaml_stream
        )

    project_name: str = (
        config_content.get("pipeline", {})
        .get("name", "Snakemake_Pipeline")
        .replace(" ", "")
        .replace("-", "_")
        .capitalize()
    )
    project_tag: str = (
        config_content.get("pipeline", {}).get("tag", "unknown").replace(".", "_")
    )
    job_name: str = (
        f"{project_name}_version_{project_tag}"
        if project_tag != "unknown"
        else project_name
    )

    # Build content of sbatch script
    sbatch_script_content: tuple[str] = (
        "#!/usr/bin/bash",
        "",
        "# Launch this pipeline with:",
        f"# sbatch {output}",
        "",
        "# Slurm parameters",
        f"#SBATCH --job-name='{job_name}'",
        f"#SBATCH --output='{log_dir}/%x_%j_%u.out'",
        f"#SBATCH --error='{log_dir}/%x_%j_%u.err'",
        f"#SBATCH --mem='{mem}'",
        "#SBATCH --cpus-per-task='1'",
        f"#SBATCH --time='{time}'",
        f"#SBATCH --chdir='{workdir}'",
        f"#SBATCH --partition='{queue}'",
        f"#SBATCH --comment='Snakemake launcher for {job_name.replace('_', ' ')}'",
        "",
        "# Ensure bash works properly or stops",
        "set -eiop 'pipefail'",
        "shopt -s nullglob",
        "",
        f"BIGR_DEFAULT_TMP='{tmp_dir}'",
        "",
        "# Used locally on Flamingo",
        "if [ -v ${BIGR_DEFAULT_TMP} ]; then",
        f"  BIGR_DEFAULT_TMP='{tmp_dir}'",
        "fi",
        "export BIGR_DEFAULT_TMP",
        "",
        "if [ -z ${BIGR_DEFAULT_TMP} ]; then",
        f"  BIGR_DEFAULT_TMP='{tmp_dir}'",
        "  export BIGR_DEFAULT_TMP",
        "fi",
        "",
        "# Used in many bash / Python scripts",
        "if [ -z ${TMP} ]; then",
        "  declare -x TMP",
        f"  TMP='{tmp_dir}'",
        "  export TMP",
        "fi",
        "",
        "# Used in some bash / R / perl / Python scripts",
        "if [ -z ${TEMP} ]; then",
        "  declare -x TEMP",
        f"  TEMP='{tmp_dir}'",
        "  export TEMP",
        "fi",
        "",
        "# Used in some bash / R / perl / Python scripts",
        "if [ -z ${TMPDIR} ]; then",
        "  declare -x TMPDIR",
        f"  TMPDIR='{tmp_dir}'",
        "  export TMPDIR",
        "fi",
        "",
        "# Used in some bash / R / perl scripts",
        "if [ -z ${TEMPDIR} ]; then",
        "  declare -x TEMPDIR",
        f"  TEMPDIR='{tmp_dir}'",
        "  export TEMPDIR",
        "fi",
        "",
        "# Used in nextflow / java scripts",
        'if [ -z "${_JAVA_OPTIONS}" ]; then',
        "  declare -x _JAVA_OPTIONS",
        f"  _JAVA_OPTIONS='-Djava.io.tmpdir=\"{tmp_dir}\"'",
        "  export _JAVA_OPTIONS",
        "fi",
        "",
        "# Declare snakemake cache directory. Used to avoid indexation steps and redundant operations",
        f"declare -x SNAKEMAKE_OUTPUT_CACHE='{snakemake_cache}'",
        "# Declare conda cache directory. Used to avoid conda reinstallations",
        f"declare -x CONDA_CACHE_PATH='{conda_cache}'",
        "# Export previously defined variables to current environment",
        "export SNAKEMAKE_OUTPUT_CACHE",
        "",
        "# Logging details",
        "date",
        "hostname",
        "",
        "# Conda environment",
        f"source '{conda_sh}'",
        f"source '{mamba_sh}'",
        f"conda activate '{conda_env}'",
        "",
        "# Run pipeline",
        f"snakemake --profile '{profile}'",
    )

    # Save sbatch script
    with open(output, "w") as sbatch_script_stream:
        sbatch_script_stream.write("\n".join(sbatch_script_content))

    if verbose:
        console.print(":ballot_box_with_check: Sbatch script available", style="green")


if __name__ == "__main__":
    sbatch_creator()
