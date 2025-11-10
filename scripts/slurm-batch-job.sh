#!/bin/bash
#SBATCH --job-name=koocad_batch
#SBATCH --output=logs/koocad_%A_%a.out
#SBATCH --error=logs/koocad_%A_%a.err
#SBATCH --array=0-99
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --partition=compute

# KooCAD Batch Job Template for Slurm + Apptainer
# This script runs parametric CAD generation jobs in parallel

set -e

echo "=========================================="
echo "KooCAD Batch Job"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "=========================================="

# Configuration
CONTAINER_IMAGE="${CONTAINER_IMAGE:-/shared/containers/koocad.sif}"
PARAM_DIR="${PARAM_DIR:-/shared/koocad/params}"
OUTPUT_DIR="${OUTPUT_DIR:-/shared/koocad/results}"
PARAM_FILE="${PARAM_DIR}/params_${SLURM_ARRAY_TASK_ID}.json"

# Database and storage configuration
export DATABASE_URL="${DATABASE_URL:-postgresql://koocad:password@db-server:5432/koocad}"
export REDIS_URL="${REDIS_URL:-redis://cache-server:6379/0}"
export MINIO_ENDPOINT="${MINIO_ENDPOINT:-storage-server:9000}"
export MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY}"
export MINIO_SECRET_KEY="${MINIO_SECRET_KEY}"

# Create output directory
TASK_OUTPUT_DIR="${OUTPUT_DIR}/${SLURM_ARRAY_JOB_ID}/${SLURM_ARRAY_TASK_ID}"
mkdir -p "$TASK_OUTPUT_DIR"

echo ""
echo "Configuration:"
echo "  Container: $CONTAINER_IMAGE"
echo "  Parameter file: $PARAM_FILE"
echo "  Output directory: $TASK_OUTPUT_DIR"
echo ""

# Check if parameter file exists
if [ ! -f "$PARAM_FILE" ]; then
    echo "Error: Parameter file not found: $PARAM_FILE"
    exit 1
fi

# Run CAD generation
echo "Starting CAD generation..."
apptainer exec \
    --bind "$OUTPUT_DIR:/output" \
    --bind "$PARAM_DIR:/params" \
    --env DATABASE_URL="$DATABASE_URL" \
    --env REDIS_URL="$REDIS_URL" \
    --env MINIO_ENDPOINT="$MINIO_ENDPOINT" \
    --env MINIO_ACCESS_KEY="$MINIO_ACCESS_KEY" \
    --env MINIO_SECRET_KEY="$MINIO_SECRET_KEY" \
    "$CONTAINER_IMAGE" \
    koocad generate \
        --params "/params/params_${SLURM_ARRAY_TASK_ID}.json" \
        --output "/output/${SLURM_ARRAY_JOB_ID}/${SLURM_ARRAY_TASK_ID}" \
        --format step stl dyna \
        --mesh-quality high

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Job completed successfully!"
    echo "Results saved to: $TASK_OUTPUT_DIR"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "Job failed with exit code: $EXIT_CODE"
    echo "=========================================="
fi

exit $EXIT_CODE
