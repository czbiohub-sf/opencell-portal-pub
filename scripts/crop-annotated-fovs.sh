#!/bin/sh
#
mode="$1"
kind="$2"

# crop ROIs from only newly-annotated FOVs (i.e., those without existing ROIs)
if [[ $kind == "new" ]]
then
    # absence of the --process-all flag here means that only newly-annotated FOVs will be cropped
    ocmi --mode $mode --crop-annotated-roi

    # generate ROI thumbnails (again only for newly-annotated FOVs)
    ocmi --mode $mode --generate-annotated-roi-thumbnails --thumbnail-scale 3 --thumbnail-quality 90

# re-crop all of the annotated FOVs (new and existing)
elif [[ $kind == "all" ]]
then
    ocdb --mode $mode --execute "delete from microscopy_fov_result where kind like 'annotated%';"
    ocdb --mode $mode --execute "delete from microscopy_fov_roi_thumbnail where roi_id is not null;"
    ocdb --mode $mode --execute "delete from microscopy_fov_roi where kind = 'annotated';"

    ocmi --mode $mode --crop-annotated-roi --process-all
    ocmi --mode $mode --generate-annotated-roi-thumbnails --thumbnail-scale 3 --thumbnail-quality 90
fi
