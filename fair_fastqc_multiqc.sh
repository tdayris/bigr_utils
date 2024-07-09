#!/usr/bin/bash

set -euiop 'pipefail'

date
hostname

SCRIPT_DIR=$(readlink -e $(dirname "${BASH_SOURCE[0]}"))

conda activate '/mnt/beegfs/userdata/t_dayris/anaconda/envs/snakemake'


python3 "${SCRIPT_DIR}/project_deploy.py" \
    "fair_fastqc_multiqc" \
    --verbose

python3 "${SCRIPT_DIR}/project_genomes.py" \
    --verbose

python3 "${SCRIPT_DIR}/project_config.py" \
    --verbose

python3 "${SCRIPT_DIR}/project_sbatch.py" \
    --time "0-08:00:00" \
    --verbose

python3 "${SCRIPT_DIR}/project_tree.py"