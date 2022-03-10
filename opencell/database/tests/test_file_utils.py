
import pandas as pd
from opencell.database import file_utils


def test_load_pipeline_microscopy_dataset_metadata(fov_metadata_redos_filepath, tmp_path):

    # the test fov-metadata CSV should not have a sort_count column
    fov_metadata = pd.read_csv(fov_metadata_redos_filepath)
    assert 'sort_count' not in fov_metadata.columns

    # load the fov-metadata CSV
    loaded_fov_metadata = file_utils.load_pipeline_microscopy_dataset_metadata(
        fov_metadata_redos_filepath
    )
    assert fov_metadata.shape[0] == loaded_fov_metadata.shape[0]

    # check that the sort_count column was backfilled
    assert 'sort_count' in loaded_fov_metadata.columns
    assert set(loaded_fov_metadata.sort_count) == set([1])

    # check that an existing sort_count column is not touched
    sort_count = 2
    tmp_filepath = tmp_path / 'fov-metadata.csv'
    fov_metadata['sort_count'] = sort_count
    fov_metadata.to_csv(tmp_filepath)
    loaded_fov_metadata = file_utils.load_pipeline_microscopy_dataset_metadata(tmp_filepath)
    assert set(loaded_fov_metadata.sort_count) == set([sort_count])

    # check that manually flagged rows are dropped
    fov_metadata.at[0, 'manually_flagged'] = True
    fov_metadata.to_csv(tmp_filepath)
    loaded_fov_metadata = file_utils.load_pipeline_microscopy_dataset_metadata(tmp_filepath)
    assert loaded_fov_metadata.shape[0] == (fov_metadata.shape[0] - 1)

    # check that all rows are dropped if all are flagged
    fov_metadata['manually_flagged'] = True
    fov_metadata.to_csv(tmp_filepath)
    loaded_fov_metadata = file_utils.load_pipeline_microscopy_dataset_metadata(tmp_filepath)
    assert loaded_fov_metadata.shape[0] == 0
