#!/bin/bash
# Build script for KooCAD Apptainer containers

set -e

echo "======================================"
echo "Building KooCAD Apptainer Containers"
echo "======================================"

# Check if apptainer is installed
if ! command -v apptainer &> /dev/null; then
    echo "Error: apptainer is not installed"
    echo "Please install apptainer: https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi

echo ""
echo "Building production container..."
apptainer build --fakeroot koocad.sif koocad.def

echo ""
echo "Building development container..."
apptainer build --fakeroot koocad-dev.sif koocad-dev.def

echo ""
echo "======================================"
echo "Build completed successfully!"
echo "======================================"
echo ""
echo "Container images:"
echo "  - koocad.sif (production)"
echo "  - koocad-dev.sif (development)"
echo ""
echo "Usage examples:"
echo ""
echo "  # Run production container"
echo "  apptainer exec koocad.sif koocad --version"
echo ""
echo "  # Development with bind mounts"
echo "  apptainer shell --bind \$(pwd)/src:/opt/koocad/src koocad-dev.sif"
echo ""
echo "  # Run tests"
echo "  apptainer exec --bind \$(pwd):/work koocad-dev.sif pytest /work/tests"
echo ""
