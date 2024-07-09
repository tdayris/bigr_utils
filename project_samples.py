# coding: utf-8

import re

from collections import defaultdict
from functools import partial
from pathlib import Path
from more_itertools import chunked_even
from rich.console import Console


def filter_regex(regex: str, paths: list[Path], console: Console, verbose: bool = True) -> tuple[list[Path]]:
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
    kept: list[str] = [path for path in paths if regex.match(path.resolve())]
    not_kept: list[str] = [path for path in paths if not regex.match(path.resolve())]
    
    if verbose:
        console.print(
            f"Out of {len(paths)} paths, "
            f"{len(kept)} answered {regex.pattern}, "
            f"{len(not_kept)} did not."
        )

    return (kept, not_kept)


def flag_identical_names(paths: list[Path], console: Console, verbose: bool = True) -> dict[str, list[Path]]:
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
        sample for sample, paths in result.items() 
        if len(paths) > 1
    ]
    result["unique"] = [
        sample for sample, paths in result.item() 
        if len(paths) == 1
    ]

    if verbose:
        console.print(
            "Based on the file names uniquely, "
            f"among {len(paths)} samples, "
            f"{len(result['duplicated'])} were flagged as duplicates or sequenced over multiple runs, "
            f"while {len(result['unique'])} remained likely unique."
        )

    return result

def detect_pattern(paths: list[Path], regex: str, console: Console, verbose: bool = True) -> tuple[list[Path] | None]:
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
    answering, not_answering = filter_regex(paths, regex, verbose)
    if len(answering) > 0:
        return (answering, not_answering, )
    return (None, paths)

detect_fastq = partial(detect_pattern, regex="(_|\.)?f(ast)?q(\.gz)?$")
detet_capture_kit = partial(detect_pattern, regex="(_|\.)bed(\.gz)?")
detect_index = partial(detect_pattern, regex="_I[\d+](_|\.)")
detect_R1_strand = partial(detect_pattern, regex="_R?1(_|\.)?")
detect_R2_strand = partial(detect_pattern, regex="_R?2(_|\.)?")

def filter_non_fastq_files(paths: list[Path], annotation: dict[str, list[str]], console: Console, verbose: bool = True) -> tuple[list[str], dict[str, list[str]]]:
    """
    Annotate and remove non-fastq files from the list of paths

    Parameters
    paths       list[str]           : List of paths to filter
    annotation  dict[str, list[str]]: Annotated files

    Return:
    list[str]               Filtered paths
    dict[str, list[str]]    Annotated files
    """
    fastq_files, other_files = detect_fastq(paths)
    if isinstance(other_files, list) and len(other_files) >= 1:
        # Deal with capture-kit file
        bed_files, other_files = detet_capture_kit(other_files)
        
        if bed_files is None:
            if verbose:
                console.print("There were no bed files (flagged as suspected capture kit file)")

        elif isinstance(bed_files, list) and len(bed_files) == 1:
            if verbose:
                console.print("File flagged as suspected capture kit: {bed_files=}")
            annotation["capture_kit_bed"] = bed_files
            annotation["non_fastq_files"] = list(sorted(other_files))

        else:
            annotation["non_fastq_files"] = list(sorted(bed_files))
        
        # Keep track of remaining files (xml, txt, ...)
        if isinstance(other_files, list) and len(other_files) >= 1:
            annotation["non_fastq_files"] += list(sorted(other_files))

    return fastq_files, annotation


def filter_index_fastq_files(paths: list[Path], annotation: dict[str, list[str]], console: Console, verbose: bool = True) -> tuple[list[str], dict[str, list[str]]]:
    """
    Annotate and remove fastq index files from the list of paths

    Parameters
    paths       list[str]           : List of paths to filter
    annotation  dict[str, list[str]]: Annotated files

    Return:
    list[str]               Filtered paths
    dict[str, list[str]]    Annotated files
    """
    fastq_index_sequences, fastq_read_sequences = detect_index(paths)
    if fastq_index_sequences:
        # Keep track of index sequences
        if len(fastq_index_sequences) == len(fastq_read_sequences):
            if verbose:
                console.print("It seems there are as much index files as read files, library seems single-ended.")
            
            # Library is single-ended
            annotation["upstream_file"] = list(sorted(fastq_read_sequences))
            annotation["index"] = list(sorted(fastq_index_sequences))

            return (None, annotation)
        
        elif len(fastq_index_sequences) == (len(fastq_read_sequences) / 2):
            if verbose:
                console.print("It seems there are half index files as read files, library seems pair-ended.")
            
            # Library is pair-ended
            annotation["index"] = list(sorted(fastq_index_sequences))
            fastq_read_sequences = chunked_even(sorted(fastq_read_sequences), 2)
            annotation["upstream_file"] = [fastq[0] for fastq in fastq_read_sequences]
            annotation["downstream_file"] = [fastq[1] for fastq in fastq_read_sequences]

            return (None, annotation)

        else:
            if verbose:
                console.print("Could not link index files and the rest of fastq files")
            fastq_read_sequences = sorted(fastq_read_sequences + fastq_index_sequences)

            return (fastq_read_sequences, annotation)
    
    if verbose:
        console.print("No index identified")
    return (paths, annotation)


def annotate_paths(paths: list[Path], console: Console, verbose: bool = True) -> dict[str, dict[str, list[str]]]:
    """
    From a given list of paths, identify pairs, indexes, resequencings and
    sample names.
    """
    annotation: dict[str, list[str]] = defaultdict(list)

    # Drop duplicated paths
    paths: list[Path] = list(set(paths))

    # Deal with non-fastq files
    fastq_files, annotation = filter_non_fastq_files(paths, annotation.copy())

    # Deal with index/primer files
    fastq_read_sequences, annotation = filter_index_fastq_files(fastq_files, annotation.copy())

    if fastq_read_sequences: 
        # Search pairs of files
        upstream_fastq, other_fastq = detect_R1_strand(fastq_read_sequences)
        downstream_fastq, other_fastq = detect_R2_strand(other_fastq)

        if len(upstream_fastq) == len(downstream_fastq):
            # Some files can be paired
            if verbose:
                console.log("We found pairs of files")
            annotation["upstream_file"] = sorted(upstream_fastq + other_fastq)
            annotation["downstream_file"] = sorted(downstream_fastq)

        else:
            if verbose:
                console.log("Could not find any pairs of file(s) with confidence")
            annotation["upstream_file"] = sorted(fastq_read_sequences)
