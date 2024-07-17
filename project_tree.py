# coding: utf-8


from rich.markup import escape
from pathlib import Path
from rich import print
from rich.filesize import decimal
from rich.text import Text
from rich.tree import Tree
from typing import Generator
from rich.console import Console

import rich_click as click
import os
import sys


def walkthrough(directory: Path, tree: Tree, skip_hidden: bool = False) -> None:
    """
    Recursively build a Tree with directory contents.
    https://github.com/Textualize/rich/blob/master/examples/tree.py
    """
    # Sort dirs first then by filename
    paths = sorted(
        Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    for path in paths:
        if skip_hidden and path.name.startswith("."):
            continue

        if path.is_dir():
            branch = tree.add(
                f":open_file_folder: [link file://{path.resolve()}]{escape(path.name)}",
                style="green",
                guide_style="cyan",
            )
            walkthrough(path, branch)
        else:
            icon: str = ":bookmark_tabs:"
            description: str = "\t"
            if (path.name == "Snakefile") or (path.suffix in (".smk")):
                icon = ":snake:"
                description += "Snakemake script"
            elif path.suffix == ".py":
                icon = ":snake:"
                description += "Python script"
            elif path.suffix == ".pyc":
                icon = ":snake:"
                description += "Python binary file"
            elif path.suffix == ".log":
                icon = ":newspaper:"
                description += "Logging file"
            elif path.suffix in (".png", ".svg", ".pdf"):
                icon = ":bar_chart:"
                description += "Chart image"
            elif path.suffix in (".md", ".rst", ".txt"):
                icon = ":regional_indicator_m:"
                description += "Text ressource"
            elif path.suffix in (".rst", ".txt"):
                icon = ":regional_indicator_t:"
                description += "Text ressource"
            elif path.suffix in (".R", ".Rmd", ".r", ".rmd"):
                icon = ":regional_indicator_r:"
                description += "R script"
            elif path.suffix in (".sh", ".bash", ".sbatch", ".zsh"):
                icon = ":scroll:"
                description += "Shell script"
            elif path.suffix in (".csv", ".tsv", ".xlsx"):
                icon = ":input_numbers:"
                description += "Table"
            elif path.suffix in (".bam", ".sam", ".cram", ".bai"):
                icon = ":dna:"
                description += "Alignment file"
            elif path.suffix in (".json", ".yaml", ".yml"):
                icon = ":receipt:"
                description += "Configuration file"
            elif path.name.endswith((".fq", ".fastq", ".fq.gz", ".fastq.gz")):
                icon = ":dna:"
                description += "Sequenced reads"
            elif path.name.endswith((".bed", ".bed.gz", ".gtf", ".gff", ".gff3")):
                icon = ":input_numbers:"
                description += "Genomic intervals"
            elif path.name.endswith((".fasta", ".fa", ".fna", ".fai", ".dict", ".bt2")):
                icon = ":dna:"
                description += "Genomic sequences"
            elif path.suffix == ".html":
                icon = ":globe_showing_europe-africa:"
                description += "HTML report"
            elif path.name.endswith(
                (
                    ".bcf",
                    ".vcf",
                    ".vcf.gz",
                    ".gvcf",
                    ".gvcf.gz",
                    ".maf",
                    ".vcf.gz.tbi",
                    ".vcf.gz.csi",
                    ".ubcf",
                )
            ):
                icon = ":dna:"
                description += "Variants description"
            elif path.suffix == ".bin":
                icon = ":computer_disk:"
                description += "Binary file"
            else:
                description = ""

            size: str = str(decimal(path.stat().st_size))

            tree.add(
                f"{icon} [link file://{path.resolve()}]{escape(path.name)}\t({size}){description}",
                style="white",
                guide_style="cyan",
            )


def check_path(path: str) -> None:
    """Check if a path exists"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")


@click.command(context_settings={"show_default": True})
@click.option("-d", "--directory", default=os.getcwd(), type=click.Path())
@click.option("-s", "--skip_hidden", is_flag=True, default=False)
def tree(directory: str = os.getcwd(), skip_hidden: bool = False) -> None:
    """Produce an annotated tree of the target directory"""
    console = Console()

    try:
        check_path(directory)
    except FileNotFoundError:
        console.print_exception(show_locals=True)
        sys.exit(1)

    if isinstance(directory, str):
        directory = Path(directory)

    tree = Tree(
        f":open_file_folder: [link file://{directory.resolve()}]{directory}",
        guide_style="cyan",
    )
    walkthrough(directory, tree, skip_hidden)
    print(tree)


if __name__ == "__main__":
    tree()
