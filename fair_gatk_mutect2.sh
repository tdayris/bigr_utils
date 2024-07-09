#!/usr/bin/bash

set -euiop 'pipefail'

date
hostname

SCRIPT_DIR=$(readlink -e $(dirname "${BASH_SOURCE[0]}"))

conda shell.bash activate '/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/shared_install/snakemake/'


python3 "${SCRIPT_DIR}/project_deploy.py" \
    "fair_gatk_mutect2" \
    --verbose

python3 "${SCRIPT_DIR}/project_genomes.py" \
    --verbose

python3 "${SCRIPT_DIR}/project_config.py" \
    --verbose

python3 "${SCRIPT_DIR}/project_sbatch.py" \
    --time "1-00:00:00" \
    --verbose

python3 "${SCRIPT_DIR}/project_tree.py"