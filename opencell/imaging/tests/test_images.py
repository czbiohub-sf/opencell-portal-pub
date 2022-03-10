import imageio
import os

from opencell.imaging.images import RawPipelineTIFF
from opencell.tests.fixtures.image_fixtures import *  # noqa: F403


def parse_validate_split(tiff):
    tiff.parse_micromanager_metadata()
    tiff.validate_micromanager_metadata()
    tiff.split_channels()


def test_parse_and_validate_v1_metadata(raw_v1_tiff):

    tiff = RawPipelineTIFF(raw_v1_tiff)
    parse_validate_split(tiff)

    assert tiff.did_split_channels
    assert tiff.global_metadata['mm_metadata_version'] == 'v1'
    assert tiff.global_metadata['exposure_time_488'] == 495


def test_parse_and_validate_v2_metadata(raw_v2_tiff):
    tiff = RawPipelineTIFF(raw_v2_tiff)
    parse_validate_split(tiff)

    assert tiff.did_split_channels
    assert tiff.global_metadata['mm_metadata_version'] == 'v2'

    # check that different exposure times were parsed from the first and last pages
    assert len(set(tiff.mm_metadata.exposure_time)) == 2


def test_parse_and_validate_with_dropped_page(raw_tiff_dropped_page):
    tiff = RawPipelineTIFF(raw_tiff_dropped_page)
    parse_validate_split(tiff)

    # the TIFF should not have been split
    assert not tiff.did_split_channels

    # check for the right error message
    messages = [
        event['message'] for event in tiff.events
        if event['message'].startswith('Channels have unequal number of slices')
    ]
    assert messages


def test_parse_and_validate_with_duplicated_metadata(raw_tiff_duplicated_metadata):
    tiff = RawPipelineTIFF(raw_tiff_duplicated_metadata)
    parse_validate_split(tiff)

    # the TIFF should have been split (because there were an even number of pages)
    assert tiff.did_split_channels

    # this opaque error message indicates that the metadata was duplicated
    messages = [event['message'] for event in tiff.events]
    assert 'Unexpected slice_ind increment 0 for channel_ind 0' in messages

    # there should be no channel-specific fields in the global metadata
    # when the metadata tags were duplicated
    assert 'exposure_time_488' not in list(tiff.global_metadata.keys())

    # check that the metadata parsed from the first and last page is the same
    assert len(set(tiff.mm_metadata.exposure_time)) == 1


def test_project_stack(full_raw_tiff, tmp_path):
    tiff = RawPipelineTIFF(full_raw_tiff)
    parse_validate_split(tiff)

    dst_filepath = os.path.join(tmp_path, 'tmp.tif')
    tiff.project_stack(channel_name='405', axis='z', dst_filepath=dst_filepath)
    tiff.project_stack(channel_name='488', axis='z', dst_filepath=dst_filepath)

    im = imageio.imread(dst_filepath)
    assert im.shape == (1024, 1024)
    assert im.dtype == 'uint16'


def test_align_cell_layer(raw_v2_tiff, tmp_path):
    tiff = RawPipelineTIFF(raw_v2_tiff)
    parse_validate_split(tiff)

    stacks, result = tiff.align_cell_layer(
        cell_layer_bottom=-5, cell_layer_top=1, step_size=0.2, bottom_wiggle_room=0
    )

    # sanity checks
    assert stacks['405'].shape == stacks['488'].shape
    assert (result['crop_window'][1] - result['crop_window'][0]) == stacks['405'].shape[0]

    # the aligned stack should be (cell_layer_top - cell_layer_bottom)/step_size = 30 slices deep
    assert stacks['405'].shape[0] == 30

    # this hard-coded value was checked by hand for the raw_v2_tiff
    assert result['cell_layer_center'] == 47

    # a too-low cell layer bottom should fail
    stacks, result = tiff.align_cell_layer(
        cell_layer_bottom=-15, cell_layer_top=1, step_size=0.2, bottom_wiggle_room=0
    )
    assert 'error' in list(result.keys())
    assert not stacks.keys()

    # a too-high cell layer top should also fail
    stacks, result = tiff.align_cell_layer(
        cell_layer_bottom=-5, cell_layer_top=55, step_size=0.2, bottom_wiggle_room=0
    )
    assert 'error' in list(result.keys())
    assert not stacks.keys()
