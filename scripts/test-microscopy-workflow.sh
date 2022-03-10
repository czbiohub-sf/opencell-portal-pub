#!/bin/sh

# Test the microscopy workflow
# This includes dataset insertion,
# FOV insertion (from both PlateMicroscopy and raw-pipeline-microscopy), and FOV processing
#
# This should be run against a truncated dev database (not a clean test database)

mode="$1"

ocdb --mode $mode --create-all

# clear the microscopy tables
ocdb --mode $mode --execute "truncate table microscopy_dataset cascade;"
ocdb --mode $mode --execute "truncate table microscopy_fov cascade;"

echo "Insert plate_microscopy datasets"
python -m opencell.scripts.insert_plate_microscopy --mode $mode --insert-datasets

echo "Construct plate_microscopy FOV metadata"
python -m opencell.scripts.insert_plate_microscopy --mode $mode --construct-metadata

echo "Insert plate_microscopy FOVs"
python -m opencell.scripts.insert_plate_microscopy --mode $mode --insert-fovs

echo "Insert PML datasets"
ocmi --mode $mode \
--snapshot-filepath ./opencell/tests/artifacts/data/metadata/2021-05-21-pipeline-microscopy-master-key-snapshot.csv \
--insert-datasets

echo "Insert FOVs for PMLs"
ocmi --mode $mode --pml-id PML0254 --insert-fovs
ocmi --mode $mode --pml-id PML0256 --insert-fovs
ocmi --mode $mode --pml-id PML0320 --insert-fovs
ocmi --mode $mode --pml-id PML0340 --insert-fovs

echo "Process all FOVs"
ocmi --mode $mode \
--process-raw-tiff \
--calculate-fov-features \
--calculate-z-profiles \
--generate-clean-tiff \
--generate-fov-thumbnails --thumbnail-scale 10 --thumbnail-quality 90

ocdb --mode $mode --inspect
