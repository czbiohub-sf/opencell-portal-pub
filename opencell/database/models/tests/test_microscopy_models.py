import pytest
import sqlalchemy as sa

from opencell.database import models


def test_microscopy_dataset_validation():

    for pml_id in ['PML0000', 'PML0001', 'PML9999', 'PML1000']:
        models.MicroscopyDataset(pml_id=pml_id, date='2021-01-01')

    for pml_id in ['PML', 'PML1', 'PML000', 'PML999', 'ML123', 'ML0001']:
        with pytest.raises(ValueError):
            models.MicroscopyDataset(pml_id=pml_id, date='2021-01-01')

    for root_dir in ['', '/some/dir', 'PlateMicroscopy']:
        with pytest.raises(ValueError):
            models.MicroscopyDataset(pml_id='PML0001', date='2021-01-01', root_directory=root_dir)


def test_microscopy_fov_validation():

    for round_id in ['R00', 'R01', 'R99']:
        models.MicroscopyFOV(pml_id='PML0001', imaging_round_id=round_id)

    for round_id in ['', 'R', 'R1', 'round1']:
        with pytest.raises(ValueError):
            models.MicroscopyFOV(pml_id='PML0001', imaging_round_id=round_id)


def test_microscopy_fov_get_result():
    pass


def test_microscopy_fov_get_score():
    pass
