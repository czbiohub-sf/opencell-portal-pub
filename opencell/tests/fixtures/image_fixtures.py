from collections import namedtuple
import json
from pathlib import Path
import pytest
import os
import skimage
import skimage.transform
import tifffile

from opencell.tests.fixtures.model_fixtures import *  # noqa: F403


# this list defines the MicroManager metadata keys on which the opencell package explicitly depends
# (via the metadata parsing methods in opencell.imaging.images.MicroManagerTiff)
MM_TAG_KEYS = [
    'SliceIndex',
    'FrameIndex',
    'ChannelIndex',
    'PositionIndex',

    # keys specific to metadata tags from MicroManager 1.x (note the missing space)
    'AndorEMCCD-Exposure',
    'AndorILE-A-Laser 405-Power Enable',
    'AndorILE-A-Laser 405-Power Setpoint',
    'AndorILE-A-Laser 488-Power Enable',
    'AndorILE-A-Laser 488-Power Setpoint',

    # keys specific to metadata tags from MicroManager 2.x
    'Andor EMCCD-Exposure',
    'Andor ILE-A-Laser 405-Power Enable',
    'Andor ILE-A-Laser 405-Power Setpoint',
    'Andor ILE-A-Laser 488-Power Enable',
    'Andor ILE-A-Laser 488-Power Setpoint',
]


def mock_raw_micromanager_tiff(
    src_filepath,
    dst_filepath,
    downsample_by=1,
    upsample=False,
    num_pages_to_drop=0,
    use_first_page_tag=False
):
    '''
    Generate a mock MicroManager-like raw TIFF from an existing MicroManager-like TIFF
    (either another mock or a true raw MicroManager TIFF)
    src_filepath :
    dst_filepath :
    downsample_by : factor by which to downsample the TIFF in x and y
    upsample : whether to upsample the TIFF back to its original 1024x1024 x-y shape
    num_pages_to_drop : number of pages to drop from (i.e., not write to) the output TIFF
        (mimics a MicroManager bug)
    use_first_page_tag : use the MicroManager metadata from the first page of the input TIFF
        on every page of the output TIFF (mimics an old MicroManager bug)

    '''
    src_tiff = tifffile.TiffFile(src_filepath)

    # define an MMTag constructor - note that the order of field names matters,
    # because the tag is passed to TiffWriter.save as a tuple
    MMTag = namedtuple('MMTag', ('code', 'dtype', 'count', 'value', 'writeonce'))
    mm_tag_code = 'MicroManagerMetadata'

    # the MM tag from the first page
    first_mm_tag_value = src_tiff.pages[0].tags[mm_tag_code].value

    pages, mm_tags = [], []
    num_pages = len(src_tiff.pages)
    for ind, page in enumerate(src_tiff.pages):

        if use_first_page_tag:
            mm_tag_value = first_mm_tag_value
        else:
            mm_tag_value = page.tags[mm_tag_code].value

        # only retain the keys we explicitly need for the tests
        # (to reduce the filesize of the mock TIFF)
        # note that we only copy the keys that exist in the original tag
        dst_mm_tag_value = {
            key: mm_tag_value[key]
            for key in set(MM_TAG_KEYS).intersection(mm_tag_value.keys())
        }
        mm_tag = MMTag(
            dtype='s',
            count=0,
            writeonce=False,
            code=mm_tag_code,
            value=json.dumps(dst_mm_tag_value)
        )

        image = page.asarray()
        if upsample:
            image = skimage.transform.resize(image, (1024, 1024), order=0, preserve_range=True)
        else:
            image = image[::downsample_by, ::downsample_by]

        mm_tags.append(tuple(mm_tag))
        pages.append(image.astype('uint16'))

    # write the TIFF
    dst_tiff = tifffile.TiffWriter(dst_filepath)
    for ind, (page, mm_tag) in enumerate(zip(pages, mm_tags)):
        if ind == (num_pages - num_pages_to_drop):
            break
        dst_tiff.save(page, extratags=[mm_tag], contiguous=False)
    dst_tiff.close()


@pytest.fixture(scope='session')
def test_images_dirpath(test_data_dirpath):
    return os.path.join(test_data_dirpath, 'microscopy')


@pytest.fixture(scope='session')
def tmp_dirpath(tmp_path_factory):
    '''
    A session-scoped temporary directory
    (the builtin pytest tmp_path fixture is function-scoped)
    '''
    return tmp_path_factory.mktemp('data')


@pytest.fixture(scope='session')
def raw_v1_tiff(test_images_dirpath):
    '''
    The filepath to a 10x-downsampled raw MicroManager TIFF with v1 metadata tags
    (and 0.5um z-step size)
    '''
    return os.path.join(test_images_dirpath, 'A1_1_ATL2__mock.ome.tif')


@pytest.fixture(scope='session')
def raw_v2_tiff(test_images_dirpath):
    '''
    The filepath to a 10x-downsampled raw MicroManager TIFF with v2 metadata tags
    (and 0.2um z-step size)
    '''
    return os.path.join(
        test_images_dirpath,
        'raw-pipeline-microscopy',
        'PML0254',
        'raw_data',
        'MMStack_1019-E5-11__mock.ome.tif'
    )


@pytest.fixture(scope='session')
def full_raw_tiff(raw_v2_tiff, tmp_dirpath):
    '''
    The filepath to an upsampled raw MicroManager TIFF
    '''
    dst_filepath = os.path.join(tmp_dirpath, 'full-raw-tiff.tif')
    mock_raw_micromanager_tiff(
        raw_v2_tiff,
        dst_filepath,
        upsample=True,
        num_pages_to_drop=0,
        use_first_page_tag=False
    )
    return dst_filepath


@pytest.fixture(scope='session')
def raw_tiff_dropped_page(raw_v2_tiff, tmp_dirpath):
    '''
    Filepath to a raw TIFF with the last page dropped
    (mimics a MicroManager bug)
    '''
    dst_filepath = os.path.join(tmp_dirpath, 'raw-tiff-dropped-page.tif')
    mock_raw_micromanager_tiff(
        raw_v2_tiff,
        dst_filepath,
        upsample=False,
        num_pages_to_drop=1,
        use_first_page_tag=False
    )
    return dst_filepath


@pytest.fixture(scope='session')
def raw_tiff_duplicated_metadata(raw_v2_tiff, tmp_dirpath):
    '''
    Filepath to a raw TIFF with the MM metadata tag from the first page used for all pages
    (mimics a MicroManager bug)
    '''
    dst_filepath = os.path.join(tmp_dirpath, 'raw-tiff-duplicated-metadata.tif')
    mock_raw_micromanager_tiff(
        raw_v2_tiff,
        dst_filepath,
        upsample=False,
        num_pages_to_drop=0,
        use_first_page_tag=True
    )
    return dst_filepath
