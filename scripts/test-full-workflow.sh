#!/bin/sh

# Test the basic metadata insertion commands,
# the PlateMicroscopy metadata construction and insertion,
# and the microscopy FOV processing
#
# This should be run against a clean test database


echo "Populate database with crispr designs and cell lines"
ocdb --mode test --clear-all
ocdb --mode test --create-all
python -m opencell.scripts.populate_db --mode test

echo "Insert plate microscopy datasets"
python -m opencell.scripts.insert_plate_microscopy --mode test --insert-datasets

echo "Construct plate microscopy metadata"
python -m opencell.scripts.insert_plate_microscopy --mode test --construct-metadata

echo "Insert plate microscopy metadata"
python -m opencell.scripts.insert_plate_microscopy --mode test --insert-fovs

echo "Process raw tiffs"
ocmi --mode test --process-raw-tiff

echo "Calculate fov features"
ocmi --mode test --calculate-fov-features

ocdb --mode test --inspect
