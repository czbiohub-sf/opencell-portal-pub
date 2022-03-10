import os
import pytest
import pandas as pd
import sqlalchemy as sa

from opencell.database import models, fov_operations, utils


def test_insert_microscopy_dataset(session):

    # create a row of the 'pipeline-microscopy-master-key' spreadsheet
    # with only the required columns, plus a 'notes' column
    root_directory = 'raw_pipeline_microscopy'
    row = pd.Series(dict(pml_id='PML0001', date='2021-01-01', notes='some notes'))

    fov_operations.insert_microscopy_dataset(session, row, root_directory, update=False)
    dataset = session.query(models.MicroscopyDataset).one()
    assert dataset.pml_id == row.pml_id
    assert dataset.date.strftime('%Y-%m-%d') == row.date

    # inserting a modified dataset with update=False should do nothing
    row.date = '2021-12-12'
    fov_operations.insert_microscopy_dataset(session, row, root_directory, update=False)
    dataset = session.query(models.MicroscopyDataset).one()
    assert dataset.pml_id == row.pml_id
    assert dataset.date.strftime('%Y-%m-%d') != row.date

    # inserting the same dataset with update=True should update the date
    fov_operations.insert_microscopy_dataset(session, row, root_directory, update=True)
    dataset = session.query(models.MicroscopyDataset).one()
    assert dataset.date.strftime('%Y-%m-%d') == row.date


@pytest.mark.usefixtures('microscopy_datasets')
def test_insert_microscopy_fovs_full_plate(session, insert_plate, fov_metadata_full_plate):

    assert len(set(fov_metadata_full_plate.pml_id)) == 1
    assert len(set(fov_metadata_full_plate.plate_id)) == 1

    pml_id = fov_metadata_full_plate.iloc[0].pml_id
    plate_id = fov_metadata_full_plate.iloc[0].plate_id

    # insert the plate, then the FOVs
    insert_plate(plate_id)
    fov_operations.insert_microscopy_fovs(session, fov_metadata_full_plate)

    dataset = (
        session.query(models.MicroscopyDataset)
        .filter(models.MicroscopyDataset.pml_id == pml_id)
        .one()
    )

    # drop FOVs from A01 and H12, which are controls and are not in the database
    inserted_fov_metadata = fov_metadata_full_plate.loc[
        ~fov_metadata_full_plate.pipeline_well_id.isin(['A01', 'H12'])
    ]
    assert len(dataset.fovs) == inserted_fov_metadata.shape[0]


@pytest.mark.usefixtures('microscopy_datasets')
def test_insert_microscopy_fovs_redos(session, insert_plate, fov_metadata_redos):

    fov_metadata = fov_metadata_redos.copy()
    insert_plate(fov_metadata.iloc[0].plate_id)
    fov_operations.insert_microscopy_fovs(session, fov_metadata)

    # all the FOVs should be inserted
    assert len(session.query(models.MicroscopyFOV).all()) == fov_metadata.shape[0]


@pytest.mark.usefixtures('microscopy_datasets')
def test_insert_microscopy_fovs_nonexistent_pml(session, insert_plate, fov_metadata):

    # change the PML ID to one that does not exist
    fov_metadata = fov_metadata.copy()
    fov_metadata['pml_id'] = 'PML0999'
    insert_plate(fov_metadata.iloc[0].plate_id)

    # this should fail silently because add_and_commit only warns about the integrity error
    fov_operations.insert_microscopy_fovs(session, fov_metadata)
    assert len(session.query(models.MicroscopyFOV).all()) == 0


@pytest.mark.usefixtures('microscopy_datasets')
def test_insert_microscopy_fovs_nonexistent_plate_id(session, insert_plate, fov_metadata):

    fov_metadata = fov_metadata.copy()
    insert_plate(fov_metadata.iloc[0].plate_id)
    fov_metadata['plate_id'] = 'P0123'

    fov_operations.insert_microscopy_fovs(session, fov_metadata)
    assert len(session.query(models.MicroscopyFOV).all()) == 0


@pytest.mark.usefixtures('microscopy_datasets')
def test_insert_microscopy_fovs_nonexistent_sort_count(session, insert_plate, fov_metadata):
    # change the sort_count to one that does not exist

    fov_metadata = fov_metadata.copy()
    insert_plate(fov_metadata.iloc[0].plate_id)
    fov_metadata['sort_count'] = 2

    fov_operations.insert_microscopy_fovs(session, fov_metadata)
    assert len(session.query(models.MicroscopyFOV).all()) == 0
