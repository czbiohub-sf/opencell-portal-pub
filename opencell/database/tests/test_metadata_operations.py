import os
import pytest
import sqlalchemy as sa
from opencell.database import models, metadata_operations, utils


def test_get_or_create_progenitor_cell_line(session):

    name = 'progenitor'
    metadata_operations.get_or_create_progenitor_cell_line(session, name, create=True)
    lines = session.query(models.CellLine).all()
    assert len(lines) == 1
    assert lines[0].name == name
    assert lines[0].line_type.value == 'PROGENITOR'

    # test retrieving the line
    line = metadata_operations.get_or_create_progenitor_cell_line(session, name, create=False)
    assert line.name == name

    # try to get a non-existent line
    line = metadata_operations.get_or_create_progenitor_cell_line(session, 'nonexistent-name')
    assert line is None


def test_get_or_create_plate_design(session):

    # insert a plate design
    plate_id = 'P0001'
    plate_design = metadata_operations.get_or_create_plate_design(
        session, plate_id, date='2021-01-01', notes='design notes!', create=True
    )

    # was the design inserted
    assert session.query(models.PlateDesign).one().design_id == plate_id

    # can we retrieve the design
    plate_design = metadata_operations.get_or_create_plate_design(session, plate_id)
    assert plate_design.design_id == plate_id

    # create a new plate directly
    plate_id = 'P0123'
    plate_design = models.PlateDesign(design_id=plate_id)
    session.add(plate_design)
    session.commit()

    # can we retrieve the new design
    plate_design = metadata_operations.get_or_create_plate_design(session, plate_id, create=False)
    assert plate_design.design_id == plate_id

    # check that we cannot insert the same plate design again
    plate_design = models.PlateDesign(design_id=plate_id)
    session.add(plate_design)
    with pytest.raises(sa.exc.IntegrityError):
        session.commit()
    session.rollback()
    assert len(session.query(models.PlateDesign).all()) == 2

    # retrieving a non-existent plate_id should return None
    plate_design = metadata_operations.get_or_create_plate_design(session, 'P0002', create=False)
    assert plate_design is None


def test_create_crispr_designs(session, library_snapshot):

    # insert a plate
    design_id = 'P0001'
    plate_design = models.PlateDesign(
        design_id=design_id, design_date='2021-01-01', design_notes='design notes!'
    )
    utils.add_and_commit(session, plate_design)

    # insert the crispr designs from the library snapshot
    metadata_operations.create_crispr_designs(
        session, plate_design, library_snapshot, drop_existing=False
    )

    # check that we inserted 96 crispr designs
    designs = session.query(models.CrisprDesign).all()
    assert len(designs) == 96
    assert len(plate_design.crispr_designs) == 96

    # check that the designs have the expected plate_id
    plate_ids = [design.plate_design_id for design in designs]
    assert set(plate_ids) == set([design_id])

    # insert the same designs again
    metadata_operations.create_crispr_designs(
        session, plate_design, library_snapshot, drop_existing=False
    )
    designs = session.query(models.CrisprDesign).all()
    assert len(designs) == 96


def test_create_polyclonal_lines(session, library_snapshot):
    '''
    '''
    # create the plate design and crispr designs for P0001
    design_id = 'P0001'
    plate_design = models.PlateDesign(
        design_id=design_id, design_date='2021-01-01', design_notes='design notes!'
    )
    session.add(plate_design)
    metadata_operations.create_crispr_designs(
        session, plate_design, library_snapshot, drop_existing=False
    )
    # create a progenitor line
    progenitor_name = 'progenitor'
    progenitor = metadata_operations.get_or_create_progenitor_cell_line(
        session, name=progenitor_name, create=True
    )
    # create the polyclonal lines
    metadata_operations.create_polyclonal_lines(
        session, progenitor, plate_design, date='2021-01-01'
    )

    # check that we inserted the correct number of lines
    lines = session.query(models.CellLine).filter(models.CellLine.line_type == 'POLYCLONAL').all()
    assert len(lines) == 96
    assert lines[0].parent.name == progenitor_name
    assert lines[-1].parent.name == progenitor_name

    # check that the lines have the correct plate_id
    plate_ids = [line.crispr_design.plate_design_id for line in lines]
    assert set(plate_ids) == set(['P0001'])


@pytest.mark.usefixtures('plate1')
def test_insert_plate(session, library_snapshot_filepath):
    '''
    Test the high-level plate-insertion methods, insert_plate_design and insert_electroporation

    Note that the calls to insert_plate_design and insert_electroporation
    are made in the `insert_plate1` fixture
    '''
    # 96 polyclonal lines plus one progenitor line in total
    assert len(session.query(models.CellLine).all()) == 97

    lines = session.query(models.CellLine).filter(models.CellLine.line_type == 'POLYCLONAL').all()
    assert len(lines) == 96

    # check that the lines have the correct plate_id
    plate_ids = [line.crispr_design.plate_design_id for line in lines]
    assert set(plate_ids) == set(['P0001'])


@pytest.mark.usefixtures('plate1')
def test_polyclonal_line_operations_from_plate_well(session):

    plate_id = 'P0001'
    for well_id in ['A01', 'A02', 'H10']:
        ops = metadata_operations.PolyclonalLineOperations.from_plate_well(
            session, plate_id, well_id, sort_count=1
        )
        assert ops.line.crispr_design.plate_design_id == plate_id
        assert ops.line.crispr_design.well_id == well_id

    # non-existent resorted line
    line = metadata_operations.PolyclonalLineOperations.from_plate_well(
        session, plate_id, well_id, sort_count=2
    )
    assert line is None

    # non-existent plate
    line = metadata_operations.PolyclonalLineOperations.from_plate_well(
        session, 'P0123', well_id, sort_count=1
    )
    assert line is None

    # invalid well_id (this causes the query to throw an error, because well_id is an enum)
    for well_id in ['', 'A', 'A1', 'A0', 'K01']:
        session.rollback()
        with pytest.raises(sa.exc.DataError):
            line = metadata_operations.PolyclonalLineOperations.from_plate_well(
                session, plate_id, well_id, sort_count=1
            )
