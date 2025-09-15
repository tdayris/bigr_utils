# coding: utf-8

import rich_click as click
import pandas
import json
import datetime
import os
import sys

from functools import partial
from rich.console import Console
from pathlib import Path
from numpy import isnan

def hhmmss(seconds: int | float) -> str:
    """
    Return humand readable number of seconds
    """
    return str(datetime.timedelta(seconds=int(seconds)))


def nb(number: str | int | float) -> str:
    """
    Format number with 2 floating point digits
    """
    if isinstance(number, str):
        return f"{number:.2f}"
    return round(number, 2)

def extract_text(
    df: pandas.DataFrame,
    colname: str,
    unit: str,
    val: str = "mean",
    with_std: bool = True,
    seconds: bool = False,
) -> str:
    """
    Return the mean and std of a dataframe column as text
    """
    desc = df[[colname]].describe()
    val = nb(desc.loc[val][colname])
    if not isnan(val):
        if (colname == "s") and (not seconds):
            val = hhmmss(val)
        elif colname == "runtime":
            if seconds is True:
                val = val * 60
            else:
                val = hhmmss(val * 60)

        std = ""
        if with_std is True and not isnan(desc.loc["std"][colname]):
            std = nb(desc.loc["std"][colname])
            if (colname == "s") and (not seconds):
                std = hhmmss(std)
            elif colname == "runtime":
                if seconds is True:
                    std = std * 60
                else:
                    std = hhmmss(std * 60)
        if std != "":
            std = f"± {std}"

        return f"""{val} {std} {unit}""".strip()
    else:
    	return f""""""


mean_time = partial(extract_text, colname="s", unit="")
reserved_runtime = partial(extract_text, colname="runtime", unit="", with_std=False)
mean_mib_reserved = partial(extract_text, colname="mem_mib", unit="Mib")
time_at_most = partial(extract_text, colname="s", unit="", val="max", with_std=False)
mem_at_most = partial(
    extract_text, colname="max_vms", unit="Mb", val="max", with_std=False
)
mean_mem_used = partial(extract_text, colname="max_vms", unit="Mb")
max_size = partial(
    extract_text, colname="size_mb", unit="Mb", val="max", with_std=False
)
memory_wasted = partial(extract_text, colname="wasted", unit="Mb")
efficiency = partial(extract_text, colname="efficiency", unit="%")
first_quartile = partial(extract_text, unit="", val="25%", with_std=False)
median = partial(extract_text, unit="", val="50%", with_std=False)
last_quartile = partial(extract_text, unit="", val="75%", with_std=False)
min_val = partial(extract_text, unit="", val="min", with_std=False)
max_val = partial(extract_text, unit="", val="max", with_std=False)


def describe_rule(
    df: pandas.DataFrame, rule_name: str, verbose: bool, console: Console
) -> dict[str, str]:
    """
    Return text to describe rule requirements and reservation
    """
    tmp = None
    if verbose is True:
        console.print(f"Working on rule {rule_name}", style="green")

    if rule_name != "all":
        tmp = df[df["rule_name"] == rule_name].copy()
    else:
        tmp = df.copy()

    if time_at_most(tmp, seconds=True) != "" and reserved_runtime(tmp, seconds=True) != "":
        time_efficiency = nb(100 * float(time_at_most(tmp, seconds=True)) / max(float(reserved_runtime(tmp, seconds=True)), 1))
    else:
        time_efficiency = ""

    return {
        "mean_time": mean_time(tmp),
        "mean_reserved_mib": mean_mib_reserved(tmp),
        "longest_required_time": time_at_most(tmp),
        "highest_memory_requirement": mem_at_most(tmp),
        "mean_memory_requirement": mean_mem_used(tmp),
        "max_input_size": max_size(tmp),
        "mean_memory_wasted": memory_wasted(tmp),
        "mean_efficiency": efficiency(tmp),
        "reserved_runtime": reserved_runtime(tmp),
        "time_efficiency": time_efficiency,
    }


def save_as_markdown(
    description: dict[str, str], output: str | Path, verbose: bool, console: Console
) -> None:
    """
    Save the dictionary as a Markdown file
    """
    global_content = None
    with open(output, "w") as markdown_stream:
        for rule, summary in description.items():
            rule_content = [
                "",
                f"# {rule}",
                "",
                "## Memory",
                ""
                f"Requires a job with at most {summary['highest_memory_requirement']},",
                f" on average {summary['mean_memory_requirement']}, ",
                f"on Gustave Roussy's HPC Flamingo, on a {summary['max_input_size']} dataset.",
                "",
                "## Time",
                "" f"A job took {summary['longest_required_time']} to proceed,",
                f"on average {summary['mean_time']}",
                "",
                "## Efficiency",
                "",
                f"{summary['mean_reserved_mib']} was reserved,",
                f"leading to a waste of {summary['mean_memory_wasted']}.",
                "",
                f"The reservation efficiency was of {summary['mean_efficiency']} on average for RAM, ",
                f"and {summary['time_efficiency']}% for time.",
                "",
            ]
            if global_content is None:
                global_content = rule_content.copy()
            else:
                global_content += rule_content

        markdown_stream.write("\n".join(global_content))


def search_benchmarks(dir_path: str | Path, verbose: bool, console: Console):
    """
    Search and return paths to all benchmark files
    within the benchmark directory
    """
    if isinstance(dir_path, str):
        dir_path = Path(dir_path)

    for path in dir_path.iterdir():
        if path.is_dir():
            if verbose is True:
                console.print(
                    f"Looking for benchmark files in {dir_path}...", style="green"
                )

            yield from search_benchmarks(
                dir_path=path, verbose=verbose, console=console
            )

        if path.name.endswith(".tsv"):
            yield path


def concat_frames(
    paths: list[Path], verbose: bool, console: Console
) -> pandas.DataFrame:
    """
    Append multiple dataframes row by row
    """
    df = None
    for path in paths:
        if path.name.endswith("_target.tsv"):
            continue
        if verbose is True:
            console.print(f"Loading {path}...", style="green")
        tmp = pandas.read_csv(path, sep="\t", header=0)
        if df is None:
            df = tmp.copy()
        elif len(df) > 0:
            df = pandas.concat([df, tmp], axis=0)
        elif verbose is True:
            console.print(":wagning: This report had no content.", style="dark_orange")

    if verbose is True:
        console.print(f"Loaded {len(df)} benchmark reports.", style="green")

    return df.reset_index()


def preprocess(
    df: pandas.DataFrame, verbose: bool, console: Console
) -> pandas.DataFrame:
    """
    Explode required columns, compute intermediar values
    and create index
    """
    if verbose is True:
        console.print("Expanding information from the benchmarks...", style="green")
    df["rule_jobname"] = [f"{j}.{r}" for j, r in zip(df.jobid, df.rule_name)]

    # Explode resources
    resources = pandas.DataFrame(
        [
            json.loads(data.replace("'", '"')) if not isinstance(data, float) else {}
            for data in pandas.Series(df.resources.explode())
        ]
    )
    df = pandas.concat([df.copy(), resources.reset_index()], axis=1)

    # Explode size
    if verbose is True:
        console.print("Adding new information in the table...", style="green")
    df["size_mb"] = [
        sum(
            [
                i
                for i in json.loads(
                    (
                        data.replace("'", '"').values()
                        if not isinstance(data, float | str)
                        else "{}"
                    )
                )
                if i is not pandas.NA
            ]
        )
        for data in pandas.Series(df.input_size_mb.explode())
    ]

    # Replace mem_mb by mem_gb if mem_gb is not NaN (because if mem_gb is used in rule, mem_mb takes the default value which is wrong)
    df.loc[df["mem_gb"].notna(), "mem_mb"] = df["mem_gb"] * 1000

    # Efficiency
    df["efficiency"] = [
        (100 * vss) / mb if mb > 0 else 100 for vss, mb in zip(df.max_vms, df.mem_mb)
    ]
    df["wasted"] = [mb - vss if mb > 0 else 0 for vss, mb in zip(df.max_vms, df.mem_mb)]
    return df


@click.command(context_settings={"show_default": True})
@click.option(
    "-b",
    "--benchmark",
    help="Path to benchmark directory",
    default=f"{os.getcwd()}/benchmark",
    type=click.Path(),
)
@click.option(
    "-o",
    "--output",
    help="Path to output file",
    default=f"{os.getcwd()}/resources.md",
    type=click.Path(),
)
@click.option(
    "-t",
    "--table",
    help="Path to TSV formatted resources.",
    default=f"{os.getcwd()}/resources.tsv",
    type=click.Path(),
)
@click.option(
    "-c",
    "--complete",
    help="Path to complete unfiltered benchmark table",
    default=f"{os.getcwd()}/benchmark.tsv",
    type=click.Path(),
)
@click.option(
    "-v",
    "--verbose",
    help="Raise verbosity level",
    is_flag=True,
    default=False,
)
def main(
    benchmark: str | Path = f"{os.getcwd()}/benchmark",
    output: str | Path = f"{os.getcwd()}/resources.txt",
    table: str | Path = f"{os.getcwd()}/resources.csv",
    complete: str | Path = f"{os.getcwd()}/benchmark.tsv",
    verbose: bool = False,
) -> None:
    """
    Search for all extended benchmark files
    and produce a usage report more reliable than
    seff.
    """
    console = Console()
    file_list = sorted(search_benchmarks(benchmark, verbose, console))
    df: pandas.DataFrame = concat_frames(file_list, verbose, console)
    df = preprocess(df.copy(), verbose, console)
    df.to_csv(complete, sep=",", header=True, index=False)
    rules = list(set(df.rule_name))

    # Building report summary
    console.print("Summerizing reports...", style="green")
    description = {"General Pipeline": describe_rule(df, "all", verbose, console)}
    description.update(
        **{rule: describe_rule(df, rule, verbose, console) for rule in rules}
    )

    # Saving results
    console.print("Saving results...", style="green")
    df = pandas.DataFrame(description).T
    df.to_csv(table, sep=",", header=True, index=True)
    save_as_markdown(description, output, verbose, console)


if __name__ == "__main__":
    main()
