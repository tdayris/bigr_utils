#!/usr/bin/bash

set -euiop 'pipefail'
shopt -s nullglob

SCRIPT_DIR=$(readlink -e $(dirname "${BASH_SOURCE[0]}"))
BASE_DIR=$(readlink -e "${SCRIPT_DIR}/..")
PIPELINE_NAME="fair_macs2_calling"
TAG="3.0.0"

source "${SCRIPT_DIR}/common.sh"
wherewhen()

conda_activate '/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/shared_install/snakemake/'

if [ -d "${PWD}/workflow" ]; then
  python3 "${SCRIPT_DIR}/project_deploy.py" \
    "${PIPELINE_NAME}" \
    --tag "${TAG}" \
    --verbose

  rm "${PWD}/config/{samples,genomes}.csv"
  rm "${PWD}/config/config.yaml"
fi

if [ ! -f "${PWD}/config/genomes.csv" ]; then
  python3 "${SCRIPT_DIR}/project_genomes.py" \
    --verbose
fi

if [ ! -f "${PWD}/config/config.yaml" ]; then
  python3 "${SCRIPT_DIR}/project_config.py" \
    --verbose
    --params "fair_macs2_calling_deeptools_bamcoverage=--Offset 12 --ignoreDuplicates --minMappingQuality 30 --samFlagExclude 4 --ignoreForNormalization X Y MT"
fi

if [ ! -f "${PWD}/scripts/sbatch.sh" ]; then
  python3 "${SCRIPT_DIR}/project_sbatch.py" \
    --time "0-12:00:00" \
    --verbose
fi

python3 "${SCRIPT_DIR}/project_tree.py"
help_message("${PIPELINE_NAME}")
