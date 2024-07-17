# coding: utf-8

import rich_click as click
import os
import sys

from pandas import DataFrame
from rich.console import Console


def check_path(path: str) -> None:
    """Check if a path exists"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")


@click.command(context_settings={"show_default": True})
@click.option(
    "-o", "--output", type=click.Path(), default=f"{os.getcwd()}/config/genomes.csv"
)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Increase verbosity")
@click.option("-f", "--force", is_flag=True, default=False, help="Force over-writing")
@click.option(
    "-e", "--empty", is_flag=True, default=False, help="Produce an empty genome file"
)
@click.help_option("-h", "--help")
def configure_genomes(
    output: str = f"{os.getcwd()}/config/genomes.csv",
    verbose: bool = False,
    empty: bool = False,
    force: bool = False,
) -> None:
    """Deploy `genomes.csv` file"""
    console = Console()

    if verbose is True:
        console.print("Checking genome file paths...")

    # Known paths to human resources
    homo_sapiens_grch38_109: dict[str, str] = {
        # Genome information
        "species": "homo_sapiens",
        "build": "GRCh38",
        "release": "109",
        "origin": "Ensembl",
        # DNA sequences
        "dna_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.dna.fasta",
        "dna_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.dna.fasta.fai",
        "dna_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.dna.dict",
        # cDNA sequences
        "cdna_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.cdna.fasta",
        "cdna_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.cdna.fasta.fai",
        "cdna_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.cdna.dict",
        # Transcript sequences
        "transcripts_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.transcripts.fasta",
        "transcripts_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.transcripts.fasta.fai",
        "transcripts_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.transcripts.dict",
        # Known variants
        "af_only": "/mnt/beegfs/database/bioinfo/Index_DB/GATK/mutect2_gnomad_af_only/hg38/somatic-hg38_af-only-gnomad.hg38.nochr.vcf.gz",
        "af_only_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/GATK/mutect2_gnomad_af_only/hg38/somatic-hg38_af-only-gnomad.hg38.nochr.vcf.gz.tbi",
        "dbsnp": "/mnt/beegfs/database/bioinfo/Index_DB/dbSNP/homo_sapiens_GRCh38.109/homo_sapiens.GRCh38.109.all.vcf.gz",
        "dbsnp_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/dbSNP/homo_sapiens_GRCh38.109/homo_sapiens.GRCh38.109.all.vcf.gz.tbi",
        # Gene annotations
        "gtf": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.gtf",
        "gff3": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.gff3",
        # Reformatting
        "id_to_gene": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.id_to_gene.tsv",
        "t2g": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.t2g.tsv",
        "genepred": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCh38.109/homo_sapiens.GRCh38.109.genePred",
        # Known blacklists
        "blacklist": "",
        # Bowtie2 indexes
        "bowtie2_dna_index": "/mnt/beegfs/database/bioinfo/Index_DB/Bowtie/2.5.4/homo_sapiens.GRCh38.105",
        "bowtie2_transcripts_index": "",
        "bowtie2_cdna_index": "",
        # Salmon index
        "salmon_index": "",
        # Variant databases
        "CancerGeneCensus": "/mnt/beegfs/database/bioinfo/Index_DB/CancerGeneCensus/Census_allTue_Aug_31_15_11_39_2021.tsv",
        "clinvar": "/mnt/beegfs/database/bioinfo/Index_DB/ClinVar/GRCh38/clinvar_20210404.GLeaves.vcf.gz",
        "clinvar_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/ClinVar/GRCh38/clinvar_20210404.GLeaves.vcf.gz.tbi",
        "cosmic": "/mnt/beegfs/database/bioinfo/Index_DB/Cosmic/GRCh38/v98/CosmicCodingMuts_v98_GRCh38.vcf.gz",
        "cosmic_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/Cosmic/GRCh38/v98/CosmicCodingMuts_v98_GRCh38.vcf.gz.tbi",
        "dbnsfp": "/mnt/beegfs/database/bioinfo/Index_DB/dbNSFP/4.1/GRCh38/dbNSFP4.1a.txt.gz",
        "dbnsfp_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/dbNSFP/4.1/GRCh38/dbNSFP4.1a.txt.gz.tbi",
        "dbvar": "/mnt/beegfs/database/bioinfo/Index_DB/dbVar/GRCh38.variant_call.all.vcf.gz",
        "dbvar_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/dbVar/GRCh38.variant_call.all.vcf.gz.tbi",
        "exac": "/mnt/beegfs/database/bioinfo/Index_DB/Exac/release1/ExAC.r1.sites.vep.fixed.vcf.gz",
        "exac_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/Exac/release1/ExAC.r1.sites.vep.fixed.vcf.gz.tbi",
        "kaviar": "/mnt/beegfs/database/bioinfo/Index_DB/Kaviar/HG38/Kaviar-160204-Public/vcfs/Kaviar-160204-Public-hg38-trim.vcf.gz",
        "kaviar_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/Kaviar/HG38/Kaviar-160204-Public/vcfs/Kaviar-160204-Public-hg38-trim.vcf.gz.tbi",
        "oncokb": "/mnt/beegfs/database/bioinfo/Index_DB/OncoKB/OncoKB.csv",
        # Pathways and genes sets
        "CORUM": "/mnt/beegfs/database/bioinfo/Index_DB/CORUM/HomoSapiens/hsapiens.CORUM.ENSG.gmt",
        "msigdb_c1": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c1.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c2": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c2.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c3": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c3.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c4": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c4.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c5": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c5.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c6": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c6.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c7": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c7.all.v2023.1.Hs.entrez.gmt",
        "msigdb_c8": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/c8.all.v2023.1.Hs.entrez.gmt",
        "msigdb_h": "/mnt/beegfs/database/bioinfo/Index_DB/MSigDB/homo_sapiens/v2023.1/entrez/h.all.v2023.1.Hs.entrez.gmt",
        "gwascatalog": "/mnt/beegfs/database/bioinfo/Index_DB/GWASCatalog/gwas_catalog_v1.0.2-studies_r2020-05-03.tsv",
        "wikipathway": "/mnt/beegfs/database/bioinfo/Index_DB/WikiPathway/HomoSapiens/hsapiens.WP.ENSG.gmt",
    }

    # Known paths to mouse resources
    mus_musculus_grcm38_99: dict[str, str] = {
        # Genome information
        "species": "mus_musculus",
        "build": "GRCm38",
        "release": "99",
        "origin": "Ensembl",
        # DNA sequences
        "dna_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.dna.fasta",
        "dna_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.dna.fasta.fai",
        "dna_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.dna.dict",
        # cDNA sequences
        "cdna_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.cdna.fasta",
        "cdna_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.cdna.fasta.fai",
        "cdna_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/GRCm38.99.mus_musculus.cdna.dict",
        # Transcript sequences
        "transcripts_fasta": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.transcripts.fasta",
        "transcripts_fai": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.transcripts.fasta.fai",
        "transcripts_dict": "/mnt/beegfs/database/bioinfo/Index_DB/Fasta/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.transcripts.dict",
        # Known variants
        "af_only": "",
        "af_only_tbi": "",
        "dbsnp": "/mnt/beegfs/database/bioinfo/Index_DB/VCF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.all.vcf.gz",
        "dbsnp_tbi": "/mnt/beegfs/database/bioinfo/Index_DB/VCF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.all.vcf.gz.tbi",
        # Gene annotations
        "gtf": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.gtf",
        "gff3": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.gff3",
        # Reformatting
        "id_to_gene": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.id_to_gene.tsv",
        "t2g": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.t2g.tsv",
        "genepred": "/mnt/beegfs/database/bioinfo/Index_DB/GTF/Ensembl/GRCm38.99/mus_musculus.GRCm38.99.genePred",
        # Known blacklists
        "blacklist": "",
        # Bowtie2 indexes
        "bowtie2_dna_index": "",
        "bowtie2_transcripts_index": "",
        "bowtie2_cdna_index": "",
        # Salmon index
        "salmon_index": "",
        # Variant databases
        "CancerGeneCensus": "/mnt/beegfs/database/bioinfo/Index_DB/CancerGeneCensus/Census_allTue_Aug_31_15_11_39_2021.tsv",
        "clinvar": "",
        "clinvar_tbi": "",
        "cosmic": "",
        "cosmic_tbi": "",
        "dbnsfp": "",
        "dbnsfp_tbi": "",
        "dbvar": "",
        "dbvar_tbi": "",
        "exac": "",
        "exac_tbi": "",
        "kaviar": "",
        "kaviar_tbi": "",
        "oncokb": "",
        # Pathways and genes sets
        "CORUM": "",
        "msigdb_c1": "",
        "msigdb_c2": "",
        "msigdb_c3": "",
        "msigdb_c4": "",
        "msigdb_c5": "",
        "msigdb_c6": "",
        "msigdb_c7": "",
        "msigdb_c8": "",
        "msigdb_h": "",
        "gwascatalog": "",
        "wikipathway": "",
    }

    # Known paths to mouse recent resources
    mus_musculus_grcm39_109: dict[str, str] = {
        # Genome information
        "species": "mus_musculus",
        "build": "GRCm39",
        "release": "109",
        "origin": "Ensembl",
        # DNA sequences
        "dna_fasta": "",
        "dna_fai": "",
        "dna_dict": "",
        # cDNA sequences
        "cdna_fasta": "",
        "cdna_fai": "",
        "cdna_dict": "",
        # Transcript sequences
        "transcripts_fasta": "",
        "transcripts_fai": "",
        "transcripts_dict": "",
        # Known variants
        "af_only": "",
        "af_only_tbi": "",
        "dbsnp": "",
        "dbsnp_tbi": "",
        # Gene annotations
        "gtf": "",
        "gff3": "",
        # Reformatting
        "id_to_gene": "",
        "t2g": "",
        "genepred": "",
        "genepred_bed": "",
        # Known blacklists
        "blacklist": "",
        # Bowtie2 indexes
        "bowtie2_dna_index": "",
        "bowtie2_transcripts_index": "",
        "bowtie2_cdna_index": "",
        # Salmon index
        "salmon_index": "",
        # Variant databases
        "CancerGeneCensus": "",
        "clinvar": "",
        "clinvar_tbi": "",
        "cosmic": "",
        "cosmic_tbi": "",
        "dbnsfp": "",
        "dbnsfp_tbi": "",
        "dbvar": "",
        "dbvar_tbi": "",
        "exac": "",
        "exac_tbi": "",
        "kaviar": "",
        "kaviar_tbi": "",
        "oncokb": "",
        # Pathways and genes sets
        "CORUM": "",
        "msigdb_c1": "",
        "msigdb_c2": "",
        "msigdb_c3": "",
        "msigdb_c4": "",
        "msigdb_c5": "",
        "msigdb_c6": "",
        "msigdb_c7": "",
        "msigdb_c8": "",
        "msigdb_h": "",
        "gwascatalog": "",
        "wikipathway": "",
    }

    # Known paths to old human resources
    homo_sapiens_grch37_75: dict[str, str] = {
        # Genome information
        "species": "homo_sapiens",
        "build": "GRCh37",
        "release": "75",
        "origin": "Ensembl",
        # DNA sequences
        "dna_fasta": "",
        "dna_fai": "",
        "dna_dict": "",
        # cDNA sequences
        "cdna_fasta": "",
        "cdna_fai": "",
        "cdna_dict": "",
        # Transcript sequences
        "transcripts_fasta": "",
        "transcripts_fai": "",
        "transcripts_dict": "",
        # Known variants
        "af_only": "",
        "af_only_tbi": "",
        "dbsnp": "",
        "dbsnp_tbi": "",
        # Gene annotations
        "gtf": "",
        "gff3": "",
        # Reformatting
        "id_to_gene": "",
        "t2g": "",
        "genepred": "",
        "genepred_bed": "",
        # Known blacklists
        "blacklist": "",
        # Bowtie2 indexes
        "bowtie2_dna_index": "",
        "bowtie2_transcripts_index": "",
        "bowtie2_cdna_index": "",
        # Salmon index
        "salmon_index": "",
        # Variant databases
        "CancerGeneCensus": "",
        "clinvar": "",
        "clinvar_tbi": "",
        "cosmic": "",
        "cosmic_tbi": "",
        "dbnsfp": "",
        "dbnsfp_tbi": "",
        "dbvar": "",
        "dbvar_tbi": "",
        "exac": "",
        "exac_tbi": "",
        "kaviar": "",
        "kaviar_tbi": "",
        "oncokb": "",
        # Pathways and genes sets
        "CORUM": "",
        "msigdb_c1": "",
        "msigdb_c2": "",
        "msigdb_c3": "",
        "msigdb_c4": "",
        "msigdb_c5": "",
        "msigdb_c6": "",
        "msigdb_c7": "",
        "msigdb_c8": "",
        "msigdb_h": "",
        "gwascatalog": "",
        "wikipathway": "",
    }

    homo_sapiens_grch38_105: dict[str, str] = {
        # Genome information
        "species": "homo_sapiens",
        "build": "GRCh38",
        "release": "105",
        "origin": "Ensembl",
        # DNA sequences
        "dna_fasta": "",
        "dna_fai": "",
        "dna_dict": "",
        # cDNA sequences
        "cdna_fasta": "",
        "cdna_fai": "",
        "cdna_dict": "",
        # Transcript sequences
        "transcripts_fasta": "",
        "transcripts_fai": "",
        "transcripts_dict": "", 
        # Known variants
        "af_only": "",
        "af_only_tbi": "",
        "dbsnp": "",
        "dbsnp_tbi": "",
        # Gene annotations
        "gtf": "",
        "gff3": "",
        # Reformatting
        "id_to_gene": "",
        "t2g": "",
        "genepred": "",
        "genepred_bed": "",
        # Known blacklists
        "blacklist": "",
        # Bowtie2 indexes
        "bowtie2_dna_index": "",
        "bowtie2_transcripts_index": "",
        "bowtie2_cdna_index": "",
        # Salmon index
        "salmon_index": "",
        # Variant databases
        "CancerGeneCensus": "",
        "clinvar": "",
        "clinvar_tbi": "",
        "cosmic": "",
        "cosmic_tbi": "",
        "dbnsfp": "",
        "dbnsfp_tbi": "",
        "dbvar": "",
        "dbvar_tbi": "",
        "exac": "",
        "exac_tbi": "",
        "kaviar": "",
        "kaviar_tbi": "",
        "oncokb": "",
        # Pathways and genes sets
        "CORUM": "",
        "msigdb_c1": "",
        "msigdb_c2": "",
        "msigdb_c3": "",
        "msigdb_c4": "",
        "msigdb_c5": "",
        "msigdb_c6": "",
        "msigdb_c7": "",
        "msigdb_c8": "",
        "msigdb_h": "",
        "gwascatalog": "",
        "wikipathway": "",
    }

    genomes_tpl: tuple[dict[str, str]] = (
        homo_sapiens_grch38_109,
        mus_musculus_grcm39_109,
        mus_musculus_grcm38_99,
        homo_sapiens_grch37_75,
        homo_sapiens_grch38_105,
    )

    # Check each single paths provided
    for genome in genomes_tpl:
        for descriptor, file_path in genome.items():
            if descriptor in ["species", "build", "release", "origin"]:
                continue  # Skip genome descriptor

            if file_path == "":
                continue  # Skip missing files

            try:
                check_path(file_path)
            except FileNotFoundError:
                console.print_exception(show_locals=True)
                sys.exit(1)

    # Save valid paths
    genomes = DataFrame.from_records(genomes_tpl)

    # On user request, remove known files
    if empty is True:
        genomes = genomes[["species", "build", "release"]]

    if os.path.exists(output) and (force is False):
        console.print(":warning: A genome file already exists")
    else:
        genomes.to_csv(output, sep=",", header=True, index=False)

    if verbose is True:
        console.print(":ballot_box_with_check: Genome files linked", style="green")


if __name__ == "__main__":
    configure_genomes()
