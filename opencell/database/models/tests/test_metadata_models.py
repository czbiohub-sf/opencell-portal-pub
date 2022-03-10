import pytest
import sqlalchemy as sa

from opencell.database import models


def test_plate_design_validation():
    invalid_plate_ids = [None, '', 'plate', 'a plate', '1 plate', 'PlateA', 'Plate  1']
    for plate_id in invalid_plate_ids:
        with pytest.raises(ValueError):
            models.PlateDesign(design_id=plate_id)


def test_crispr_design_validation():
    pass


def test_crispr_design_get_best_cell_line():
    pass


def test_cell_line_get_best_pulldown():
    pass


def test_cell_line_get_top_scoring_fovs():
    pass


def test_cell_line_get_best_fov():
    pass
