# coding: utf-8

import re
import rich_click as click
import os
import sys
import pandas

from collections import defaultdict
from functools import partial
from pathlib import Path
from more_itertools import chunked_even
from rich.console import Console
from typing import Generator


def filter_regex(
    regex: str, paths: list[Path], console: Console, verbose: bool = True
) -> tuple[list[Path]]:
    """
    Filter-out samples answering a given regex

    Parameters:
    regex   str       : Regular expression used to filter the list of files
    paths   list[Path]: List of files to filter
    console Console   : rich IO

    Return:
    two lists of Path
    1. files to keep
    2. filtered-out files
    """
    regex = re.compile(regex)
    kept: list[str] = [path for path in paths if regex.search(str(path.resolve()))]
    not_kept: list[str] = [
        path for path in paths if not regex.search(str(path.resolve()))
    ]

    if verbose:
        console.print(
            f"Out of {len(paths)} paths, "
            f"{len(kept)} answered {regex.pattern}, "
            f"{len(not_kept)} did not.",
            style="green",
        )

        if len(kept) == 0:
            console.print(f":warning: No files kept!", style="dark_orange")

    return (kept, not_kept)


def flag_identical_names(
    paths: list[Path], console: Console, verbose: bool = True
) -> dict[str, list[Path]]:
    """
    Find samples with identical file name and different file paths

    Parameters:
    paths   list[Path]: List of files to group

    Return:
    dictionary: key = sample file name, values = list of paths
    """
    result: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        result[path.name].append(path)

    result["duplicated"] = [
        sample for sample, paths in result.items() if len(paths) > 1
    ]
    result["unique"] = [sample for sample, paths in result.item() if len(paths) == 1]

    if verbose:
        console.print(
            "Based on the file names uniquely, "
            f"among {len(paths)} samples, "
            f"{len(result['duplicated'])} were flagged as duplicates or sequenced over multiple runs, "
            f"while {len(result['unique'])} remained likely unique.",
            style="green",
        )

    return result


def detect_pattern(
    paths: list[Path], regex: str, console: Console, verbose: bool = True
) -> tuple[list[Path] | None]:
    """
    Search for pattern in all sample names.

    Parameters:
    paths   list[Path]: List of files to check
    regex   str       : Regular expression to search

    Return:
    True if:
    1. regex exists
    2. regex exists for all or one out of two samples
    """
    answering, not_answering = filter_regex(
        paths=paths, regex=regex, verbose=verbose, console=console
    )
    if (answering is not None) or (len(answering) > 0):
        return (
            answering,
            not_answering,
        )
    return (None, paths)


detect_fastq = partial(detect_pattern, regex=r"(_|\.)?f(ast)?q(\.gz)?$")
detet_capture_kit = partial(detect_pattern, regex=r"(_|\.)bed(\.gz)?")
detect_index = partial(detect_pattern, regex=r"_I[\d+](_|\.)")
detect_R1_strand = partial(detect_pattern, regex=r"_R?1(_|\.)?")
detect_R2_strand = partial(detect_pattern, regex=r"_R?2(_|\.)?")


def filter_non_fastq_files(
    paths: list[Path],
    annotation: dict[str, list[str]],
    console: Console,
    verbose: bool = True,
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Annotate and remove non-fastq files from the list of paths

    Parameters
    paths       list[str]           : List of paths to filter
    annotation  dict[str, list[str]]: Annotated files

    Return:
    list[str]               Filtered paths
    dict[str, list[str]]    Annotated files
    """
    fastq_files, other_files = detect_fastq(
        paths=paths, console=console, verbose=verbose
    )
    if isinstance(other_files, list) and len(other_files) >= 1:
        # Deal with capture-kit file
        bed_files, other_files = detet_capture_kit(
            other_files, console=console, verbose=verbose
        )

        if bed_files is None:
            if verbose:
                console.print(
                    "There were no bed files (flagged as suspected capture kit file)",
                    style="green",
                )

        elif isinstance(bed_files, list) and len(bed_files) == 1:
            if verbose:
                console.print(
                    "File flagged as suspected capture kit: {bed_files=}", style="green"
                )
            annotation["capture_kit_bed"] = bed_files
            annotation["non_fastq_files"] = list(sorted(other_files))

        else:
            annotation["non_fastq_files"] = list(sorted(bed_files))

        # Keep track of remaining files (xml, txt, ...)
        if isinstance(other_files, list) and len(other_files) >= 1:
            annotation["non_fastq_files"] += list(sorted(other_files))

    return fastq_files, annotation


def filter_index_fastq_files(
    paths: list[Path],
    annotation: dict[str, list[str]],
    console: Console,
    verbose: bool = True,
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Annotate and remove fastq index files from the list of paths

    Parameters
    paths       list[str]           : List of paths to filter
    annotation  dict[str, list[str]]: Annotated files

    Return:
    list[str]               Filtered paths
    dict[str, list[str]]    Annotated files
    """
    fastq_index_sequences, fastq_read_sequences = detect_index(
        paths=paths, console=console, verbose=verbose
    )

    if fastq_index_sequences:
        # Keep track of index sequences
        if len(fastq_index_sequences) == len(fastq_read_sequences):
            if verbose:
                console.print(
                    "It seems there are as much index files as read files, library seems single-ended."
                )

            # Library is single-ended
            annotation["upstream_file"] = list(sorted(fastq_read_sequences))
            annotation["index"] = list(sorted(fastq_index_sequences))

            return (None, annotation)

        elif len(fastq_index_sequences) == (len(fastq_read_sequences) / 2):
            if verbose:
                console.print(
                    "It seems there are half index files as read files, library seems pair-ended.",
                    style="green",
                )

            # Library is pair-ended
            annotation["index"] = list(sorted(fastq_index_sequences))
            fastq_read_sequences = list(chunked_even(sorted(fastq_read_sequences), 2))
            annotation["upstream_file"] = [fastq[0] for fastq in fastq_read_sequences]
            annotation["downstream_file"] = [fastq[1] for fastq in fastq_read_sequences]

            return (None, annotation)

        else:
            if verbose:
                console.print(
                    "Could not link index files and the rest of fastq files",
                    style="green",
                )
            fastq_read_sequences = sorted(fastq_read_sequences + fastq_index_sequences)

            return (fastq_read_sequences, annotation)

    if verbose:
        console.print("No index identified", style="green")
    return (paths, annotation)


def annotate_paths(
    paths: list[Path], console: Console, verbose: bool = True
) -> dict[str, dict[str, list[str]]]:
    """
    From a given list of paths, identify pairs, indexes, resequencings and
    sample names.
    """
    annotation: dict[str, list[str]] = defaultdict(list)

    # Drop duplicated paths
    paths: list[Path] = list(set(paths))

    # Deal with non-fastq files
    fastq_files, annotation = filter_non_fastq_files(
        paths, annotation.copy(), console=console, verbose=verbose
    )
    if (fastq_files is None) or (len(fastq_files) == 0):
        raise FileNotFoundError("No fastq file found")

    # Deal with index/primer files
    fastq_read_sequences, annotation = filter_index_fastq_files(
        fastq_files, annotation.copy(), console=console, verbose=verbose
    )

    if fastq_read_sequences:
        # Search pairs of files
        upstream_fastq, other_fastq = detect_R1_strand(
            fastq_read_sequences, console=console, verbose=verbose
        )
        downstream_fastq, other_fastq = detect_R2_strand(
            other_fastq, console=console, verbose=verbose
        )

        if len(upstream_fastq) == len(downstream_fastq):
            # Some files can be paired
            if verbose:
                console.print("We found pairs of files", style="green")
            annotation["upstream_file"] = sorted(upstream_fastq + other_fastq)
            annotation["downstream_file"] = sorted(downstream_fastq)

        else:
            if verbose:
                console.print(
                    "Could not find any pairs of file(s) with confidence", style="green"
                )
            annotation["upstream_file"] = sorted(fastq_read_sequences)
    elif "upstream_file" not in annotation.keys():
        raise ValueError(f"No fastq file found in {paths=}")

    return annotation


def remove_common_suffixes(name: str) -> str:
    """
    Remove common suffixes from file names to guess sample names
    """
    # Remove file extension
    name = re.sub(r"(_|\.)?f(ast)?q(\.gz)?$", "", name)

    # Remove stream name
    name = re.sub(r"_R?(1|2)$", "", name)

    # Remove lane number

    name = re.sub(r"_L[0-9]+$", "", name)

    # Remove EKDN and ERDN
    name = re.sub(r"_E(K|R)DN[0-9]+", "", name)

    # Cleaning
    name = name.strip("_").strip(".")

    return name


def guess_sample_id(
    samples: pandas.DataFrame, console: Console, verbose: bool = True
) -> str:
    """
    Detect samples identifiers from sample paths
    """
    samples_id = []
    if "downstream_file" in samples.columns:
        for up, down in zip(samples.upstream_file, samples.downstream_file):
            if down != "":
                samples_id.append(
                    remove_common_suffixes(os.path.commonprefix([up.name, down.name]))
                )
            else:
                samples_id.append(remove_common_suffixes(up.name))
    else:
        for up in samples.upstream_file:
            samples_id.append(remove_common_suffixes(name))

    return samples_id


def as_dataframe(
    annotated: dict[str, list[str]],
    console: Console,
    organism: str = "homo_sapiens.GRCh38.105",
    verbose: bool = True,
) -> pandas.DataFrame:
    """
    Format annotation table as required by pipelines
    """
    samples = pandas.DataFrame.from_dict(
        {
            "upstream_file": annotated["upstream_file"],
            "downstream_file": annotated["downstream_file"],
        }
    )
    species, build, release = organism.split(".")
    samples["species"] = species
    samples["build"] = build
    samples["release"] = release
    samples["sample_id"] = guess_sample_id(
        samples=samples.copy(), verbose=verbose, console=console
    )
    samples.set_index("sample_id", inplace=True)

    if verbose:
        shape: tuple[int] = samples.shape
        if shape[0] == 1:
            console.print(
                f"{shape[0]} sample was identified and annotated.", style="green"
            )
        else:
            console.print(
                f"{shape[0]} samples were identified and annotated.", style="green"
            )

    return samples


def search_files_locally(
    path: str | Path, verbose: bool, console: Console
) -> Generator[Path, None, None]:
    """
    Yield all availabe files in the repository and its sub-repositories
    """
    if isinstance(path, str):
        path = Path(path)

    if verbose:
        console.print(f"Searching in {path.resolve()}", style="green")

    for content in path.iterdir():
        if content.name in (".git", ".snakemake"):
            continue

        elif content.is_dir():
            yield from search_files_locally(
                path=content, verbose=verbose, console=console
            )

        if verbose:
            console.print(f"Found {content.resolve()}", style="green")
        yield content


def search_files_on_iRODS(
        project_id: str | list[str], verbose: bool, console: Console
    ) -> Generator[Path, None, None]:
    """
    Yeld all available files on iRODS under the given project ID
    """
    ssl_settings = {}
    env_file: str = Path('~/.irods/irods_environment.json').expanduser()
    if not Path(env_file).exists():
        raise FileNotFoundError(
            f"Could not find {env_file=}. "
            "Use `iinit` in your terminal."
        )

    if isinstance(project_id, str):
        project_id = [project_id]

    if verbose:
        console.log(f"Searching for {project_id=} on iRODS")

    for project in project_id:
        with iRODSSession(irods_env_file=env_file, **ssl_settings) as session:
            # iRODS query, this takes several seconds
            collections: session.query = (
                session.query(Collection, CollectionMeta)
                       .filter(Criterion("=", CollectionMeta.name, "projectName"))
                       .filter(Criterion("=", CollectionMeta.value, project))
            )

            # Parse query, this takes 2 seconds
            for collection in collections:
                for sub_coll in session.collections.get(collection[Collection.name]).subcollections:
                    for dataset in sub_coll.data_objects:
                        yield Path(dataset.path)


@click.command(context_settings={"show_default": True})
@click.option(
    "-d",
    "--directory",
    help="Search local files",
    default=f"{os.getcwd()}/../data_input",
    type=click.Path(),
)
@click.option(
    "-i",
    "--iRODS",
    help="iRODS project idnetifier",
    type=str,
    default="None",
)
@click.option(
    "-o",
    "--output",
    help="Path to output sample file",
    default=f"{os.getcwd()}/config/samples.csv",
    type=click.Path(),
)
@click.option(
    "--dont_guess_samples_names",
    is_flag=True,
    help="Do not let this script guess samples names and re-sequencings",
    default=False,
)
@click.option(
    "--organism",
    help="Organism which the samples belong to",
    type=click.Choice(
        [
            "homo_sapiens.GRCh38.105",
            "homo_sapiens.GRCh37.75",
            "mus_musculus.GRCm38.99",
            "mus_musculus.GRCm39.109",
            "homo_sapiens.GRCh38.109",
        ]
    ),
    default="homo_sapiens.GRCh38.105",
)
@click.option(
    "-v",
    "--verbose",
    help="Increase verbosity",
    default=False,
    is_flag=True,
)
@click.option(
    "-f",
    "--force",
    help="Force overwritting",
    default=False,
    is_flag=True,
)
@click.help_option("-h", "--help")
def main(
    directory: str | Path = f"{os.getcwd()}/../data_input",
    irods: str = "None",
    output: str | Path = f"{os.getcwd()}/config/samples.csv",
    dont_guess_samples_names: bool = False,
    organism: str = "homo_sapiens.GRCh38.105",
    verbose: bool = False,
    force: bool = False,
) -> None:
    """
    Search for files (locally or on iRODS) and annotate them
    """
    console = Console()
    file_list: list[str] = []
    if irods == "None":
        file_list = sorted(search_files_locally(directory, verbose, console))
    else:
        file_list = sorted(search_files_on_iRODS(directory, verbose, console))

    try:
        annotated: dict[str, str] = annotate_paths(
            file_list, console=console, verbose=verbose
        )
    except FileNotFoundError:
        console.print_exception(show_locals=True)
        sys.exit(1)
    except ValueError:
        console.print_exception(show_locals=True)
        sys.exit(2)

    samples: pandas.DataFrame = as_dataframe(
        annotated=annotated, organism=organism, console=console, verbose=verbose
    )
    if isinstance(output, str):
        output = Path(output)
    if not output.parent.exists():
        output.parent.mkdir(parents=True, exist_ok=True)
    if verbose:
        console.print(samples)
    if (force) or (not output.exists()):
        samples.to_csv(output, sep=",", header=True, index=True)
    else:
        console.print(":warning: Existing file not over-written", style="dark_orange")


if __name__ == "__main__":
    main()
