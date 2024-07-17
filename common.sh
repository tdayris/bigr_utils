#!/usr/bin/bash
# coding: utf-8

# This function only changes echo headers
# for user's sake.
function message() {
  # Define local variables
  local status=${1}         # Either INFO, CMD, ERROR or DOC
  local message="${2:-1}"   # Your message

  # Classic switch based on status
  if [ ${status} = INFO ]; then
    >&2 echo -e "\033[1;36m@INFO:\033[0m ${message}"
  elif [ ${status} = CMD ]; then
    >&2 echo -e "\033[1;32m@CMD:\033[0m ${message}"
  elif [ ${status} = ERROR ]; then
    >&2 echo -e "\033[41m@ERROR:\033[0m ${message}"
  elif [ ${status} = DOC ]; then
    >&2 echo -e "\033[0;33m@DOC:\033[0m ${message}"
  elif [ ${status} = WARNING ]; then
    >&2 echo -e "\033[1;33m@WARNING:\033[0m ${message}"
  else
    error_handling ${LINENO} 1 "Unknown message type: ${status}"
  fi
}

# Source then activate conda environment
function conda_activate () {
  BASE_CONDA="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/shared_install/snakemake"

  CMD="source \"${BASE_CONDA}/etc/profile.d/conda.sh\""
  message CMD "${CMD}"
  eval ${CMD}

  CMD="conda activate"
  message CMD "${CMD}"
  eval ${CMD}

  CMD="conda activate \"${1}\""
  message CMD "${CMD}"
  eval ${CMD}
}

# Log when and where the pipeline was launched
function wherewhen () {
  message INFO "Working on $(hostname) at $(date), as ${USER}"
}

# Redirect user on the right help page
function help_message() {
  message INFO "Please see official documentation at: https://github.com/tdayris/${1}/blob/main/workflow/report/usage.rst"
  message INFO "Run me: sbatch ${PWD}/scripts/sbatch.sh"
  exit 1
}

# Declare snakemake cache directory. Used to avoid indexation steps and redundant operations
declare -x SNAKEMAKE_OUTPUT_CACHE="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/snakemake_cache"

# Declare conda cache directory. Used to avoid conda reinstallations
declare -x CONDA_CACHE_PATH="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/conda_cache"

declare -x SHARED_SINGULARITY_PATH="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/singularity"
declare -x SHARED_CONDA_INDSTALL="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/shared_install"

# Profile and executor
declare -x SNAKEMAKE_PROFILE_PATH="/mnt/beegfs/pipelines/unofficial-snakemake-wrappers/profiles/slurm-web-8"

# Export previously defined variables to current environment
export SNAKEMAKE_OUTPUT_CACHE CONDA_ENV_PATH CONDA_CACHE_PATH SNAKEMAKE_PROFILE_PATH

CMD="mkdir --parents --verbose tmp/shadow"
message CMD "${CMD}"
eval ${CMD}

# Overloading TMP directories
# Our main temporary directory.
if [ -z "${BIGR_DEFAULT_TMP:-}" ]; then
  declare -x BIGR_DEFAULT_TMP
  BIGR_DEFAULT_TMP="/mnt/beegfs/userdata/${USER}/tmp"
  export BIGR_DEFAULT_TMP
elif [ "${BIGR_DEFAULT_TMP:-}" == "/tmp" ]; then
  BIGR_DEFAULT_TMP="/mnt/beegfs/userdata/${USER}/tmp"
  export BIGR_DEFAULT_TMP
fi

if [ ! -d "${BIGR_DEFAULT_TMP}" ]; then
  CMD="mkdir --parent --verbose ${BIGR_DEFAULT_TMP}"
  message CMD "${CMD}"
  eval ${CMD}
fi

# Used in many bash / Python scripts
if [ -z "${TMP:-}" ]; then
  message WARNING "TMP environment variable was not set. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TMP now points to ${BIGR_DEFAULT_TMP}"
  declare -x TMP
  TMP="${BIGR_DEFAULT_TMP}"
  export TMP
elif [ "${TMP:-}" == "/tmp" ]; then
  message WARNING "TMP currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "This value is now changed to ${BIGR_DEFAULT_TMP}"
  TMP="${BIGR_DEFAULT_TMP}"
  export TMP
else
  message INFO "TMP -> ${TMP}"
fi

# Used in some bash / R / perl / Python scripts
if [ -z "${TEMP:-}" ]; then
  message WARNING "TEMP environment variable was not set. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TEMP now points to ${BIGR_DEFAULT_TMP}"
  declare -x TEMP
  TEMP="${BIGR_DEFAULT_TMP}"
  export TEMP
elif [ "${TEMP:-}" == "/tmp" ]; then
  message WARNING "TEMP currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TEMP now points to ${BIGR_DEFAULT_TMP}"
  TEMP="${BIGR_DEFAULT_TMP}"
  export TEMP
else
  message INFO "TEMP -> ${TEMP}"
fi

# Used in some bash / R / perl / Python scripts
if [ -z "${TMPDIR:-}" ]; then
  message WARNING "TMPDIR environment variable was not set. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TMPDIR now points to ${BIGR_DEFAULT_TMP}"
  declare -x TMPDIR
  TMPDIR="${BIGR_DEFAULT_TMP}"
  export TMPDIR
elif [ "${TMPDIR:-}" == "/tmp" ]; then
  message WARNING "TMPDIR currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TMPDIR now points to ${BIGR_DEFAULT_TMP}"
  TMPDIR="${BIGR_DEFAULT_TMP}"
  export TMPDIR
else
  message INFO "TMPDIR -> ${TMPDIR}"
fi

# Used in some bash / R / perl scripts
if [ -z "${TEMPDIR:-}" ]; then
  message WARNING "TEMPDIR environment variable was not set. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TEMPDIR now points to ${BIGR_DEFAULT_TMP}"
  declare -x TEMPDIR
  TEMPDIR="${BIGR_DEFAULT_TMP}"
  export TEMPDIR
elif [ "${TEMPDIR:-}" == "/tmp" ]; then
  message WARNING "TEMPDIR currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "TEMPDIR now points to ${BIGR_DEFAULT_TMP}"
  TEMPDIR="${BIGR_DEFAULT_TMP}"
  export TEMPDIR
else
  message INFO "TEMPDIR -> ${TEMPDIR}"
fi

# Used in nextflow scripts
if [ -z "${NXF_TEMP:-}" ]; then
  message WARNING "NXF_TEMP environment variable was not set. This can lead to NextFlow errors due to lack of space in /tmp"
  message WARNING "NXF_TEMP now points to ${BIGR_DEFAULT_TMP}"
  declare -x NXF_TEMP
  NXF_TEMP="${BIGR_DEFAULT_TMP}"
  export NXF_TEMP
elif [ "${NXF_TEMP:-}" == "/tmp" ]; then
  message WARNING "NXF_TEMP currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "NXF_TEMP now points to ${BIGR_DEFAULT_TMP}"
  NXF_TEMP="${BIGR_DEFAULT_TMP}"
  export NXF_TEMP
else
  message INFO "NXF_TEMP -> ${NXF_TEMP}"
fi

# Used in nextflow / java scripts
if [ -z "${_JAVA_OPTIONS:-}" ]; then
  message WARNING "_JAVA_OPTIONS environment variable was not set. This can lead to Java errors due to lack of space in /tmp"
  message WARNING "_JAVA_OPTIONS now points to ${BIGR_DEFAULT_TMP}"
  declare -x _JAVA_OPTIONS
  _JAVA_OPTIONS="-Djava.io.tmpdir='${BIGR_DEFAULT_TMP}'"
  export _JAVA_OPTIONS
elif [ "${_JAVA_OPTIONS:-}" == "/tmp" ]; then
  message WARNING "_JAVA_OPTIONS currently points to '/tmp'. This can lead to OS errors due to lack of space in /tmp"
  message WARNING "_JAVA_OPTIONS now points to ${BIGR_DEFAULT_TMP}"
  _JAVA_OPTIONS="-Djava.io.tmpdir='${BIGR_DEFAULT_TMP}'"
  export _JAVA_OPTIONS
else
  message INFO "_JAVA_OPTIONS -> ${_JAVA_OPTIONS}"
fi

if [ ! -f "${HOME}/.Renviron" ]; then
  message WARNING "${HOME}/.Renviron does not exists. This can lead to OS errors in R due to lack of space in /tmp"
  message WARNING "${HOME}/.Renviron was created with: TMP = '${BIGR_DEFAULT_TMP}'"
  echo -e "TMP = '${BIGR_DEFAULT_TMP}'" > "${HOME}/.Renviron"
fi

if [ ! -f "${HOME}/.condarc" ]; then
  message WARNING "${HOME}/.condarc does not exists. This can lead to OS errors in conda due to lack of space in /tmp"
  message WARNING "${HOME}/.condarc was created with: env_dir, pkgs_dir, and conda-build:root_dir overloaded"
  echo -e "envs_dir:\n\t- /mnt/beegfs/userdata/${USER}/anaconda/envs\npkgs_dir:\n\t- /mnt/beegfs/userdata/${USER}/anaconda/pkgs\nconda-build:\n\troot_dir: /mnt/beegfs/userdata/${USER}/conda-builds" > "${HOME}/.condarc"
fi


