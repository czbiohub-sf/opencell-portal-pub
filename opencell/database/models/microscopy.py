import logging
import re
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from opencell.database.models import Base
from opencell.database.models.mixins import TimestampMixin

logger = logging.getLogger(__name__)


class MicroscopyDataset(Base):
    '''
    A confocal microscopy dataset

    These datasets are assumed to correspond to automated acquisitions
    using the confocal (dragonfly) microscope that have PML-style IDs (e.g., PML0123)

    These datasets almost always consist of images from many wells,
    but by definition consist only of images from one imaging plate.

    Note, however, that a single imaging plate may have wells from more than one pipeline plate.

    '''

    __tablename__ = 'microscopy_dataset'

    # the manually-defined pml_id (also called exp_id)
    pml_id = sa.Column(sa.String, primary_key=True)

    # the manually-defined imaging date
    date = sa.Column(sa.Date, nullable=False)

    # either 'plate_microscopy' (for the legacy 'PlateMicroscopy' directory on ESS)
    # or 'raw_pipeline_microscopy'
    # (for the 'raw-pipeline-microscopy' directory containing all datasets starting at PML0196)
    # note that the absolute path to these directories is context-dependent
    root_directory = sa.Column(sa.String)

    # all columns from the pipeline-microscopy-master-key as a JSON object
    # (for reference/convenience only)
    raw_metadata = sa.Column(postgresql.JSONB)

    # one dataset to many FOVs
    fovs = sa.orm.relationship('MicroscopyFOV', back_populates='dataset')

    @sa.orm.validates('pml_id')
    def validate_pml_id(self, key, value):
        match = re.match(r'^PML[0-9]{4}$', value)
        if match is None:
            raise ValueError('Invalid pml_id %s' % value)
        return value

    @sa.orm.validates('root_directory')
    def validate_root_directory(self, key, value):
        if value not in ['plate_microscopy', 'raw_pipeline_microscopy']:
            raise ValueError('Invalid root_directory %s' % value)
        return value


class MicroscopyFOV(Base):
    '''
    A single confocal z-stack of one field of view (FOV)

    Notes
    -----
    One entry in this table corresponds to a single raw TIFF stack
    in the 'PlateMicroscopy' directory
    For example: 'mNG96wp19/ML0137_20190528/mNG96wp19_sortday1/A9_1_BAG6.ome.tif'

    '''

    __tablename__ = 'microscopy_fov'

    id = sa.Column(sa.Integer, primary_key=True)

    # many FOVs to one cell_line
    cell_line_id = sa.Column(
        sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'), index=True
    )
    cell_line = sa.orm.relationship('CellLine', back_populates='fovs', uselist=False)

    # many FOVs to one microscopy_dataset
    pml_id = sa.Column(sa.String, sa.ForeignKey('microscopy_dataset.pml_id'))
    dataset = sa.orm.relationship('MicroscopyDataset', back_populates='fovs', uselist=False)

    # one FOV to many FOV results
    results = sa.orm.relationship(
        'MicroscopyFOVResult', back_populates='fov', passive_deletes='all'
    )

    # one FOV to many ROIs
    rois = sa.orm.relationship(
        'MicroscopyFOVROI', back_populates='fov', passive_deletes='all'
    )

    # one FOV to many thumbnails
    thumbnails = sa.orm.relationship(
        'MicroscopyFOVThumbnail', back_populates='fov', passive_deletes='all'
    )

    # one FOV to one FOV annotation
    annotation = sa.orm.relationship(
        'MicroscopyFOVAnnotation', back_populates='fov', uselist=False, passive_deletes='all'
    )

    # round_id is either 'R01' (initial post-sort imaging)
    # or 'R02' (thawed-plate imaging)
    imaging_round_id = sa.Column(sa.String, nullable=False)

    # the original site number (required to construct unique dst filenames)
    site_num = sa.Column(sa.Integer, nullable=False)

    # the path to the original raw TIFF, relative to the root_directory
    raw_filename = sa.Column(sa.String)

    # because we image by plate, each well_id is imaged once per plate
    # this fact can be expressed by the following constraint
    # (assuming that each cell line appears in only one well on each imaging plate)
    __table_args__ = (sa.UniqueConstraint(pml_id, cell_line_id, site_num),)

    @sa.orm.validates('imaging_round_id')
    def validate_imaging_round_id(self, key, value):
        match = re.match(r'^R[0-9]{2}$', value)
        if match is None:
            raise ValueError('Invalid imaging_round_id %s' % value)
        return value

    def get_result(self, kind):
        '''
        Retrieve a MicroscopyFOVResult of the given kind
        (Note that this method will be slow without eager-loading)
        '''
        result = [result for result in self.results if result.kind == kind]
        return result[0] if result else None

    def get_result_via_query(self, kind):
        '''
        Retrieve a MicroscopyFOVResult of the given kind
        This is a query-based alternative to get_result that will be faster without eager loading
        '''
        return (
            sa.orm.object_session(self)
            .query(MicroscopyFOVResult)
            .filter(MicroscopyFOVResult.fov_id == self.id)
            .filter(MicroscopyFOVResult.kind == kind)
            .one_or_none()
        )

    def get_score(self):
        features = self.get_result('fov-features')
        return features.data.get('score') if features else None

    def get_thumbnail(self):
        return self.thumbnails[0] if self.thumbnails else None


class MicroscopyFOVResult(Base, TimestampMixin):
    '''
    Various kinds of data derived from a microscopy FOV as arbitrary JSON objects

    Examples: the metadata generated by FOVProcessor.process_raw_tiff,
    or the features extracted from the Hoechst z-projection used to predict FOV scores
    '''

    __tablename__ = 'microscopy_fov_result'

    id = sa.Column(sa.Integer, primary_key=True)

    # many results to one FOV
    fov_id = sa.Column(sa.Integer, sa.ForeignKey('microscopy_fov.id', ondelete='CASCADE'))
    fov = sa.orm.relationship('MicroscopyFOV', back_populates='results', uselist=False)

    # the kind or type of the result ('raw-tiff-metadata', 'fov-features', etc)
    # (eventually, this should be changed to an enum)
    kind = sa.Column(sa.String)

    # the result data
    data = sa.Column(postgresql.JSONB)


class MicroscopyFOVROI(Base, TimestampMixin):
    '''
    An ROI cropped from a raw FOV

    These ROIs are intended specifically for the volume visualization in the frontend

    The crop can be in any or all of the x, y, and z dimensions
    (usually, all crops are at least cropped in z around the cell layer)

    Also, usually, the intensities have been normalized and downsampled to uint8,
    using the min/max intensities and (optionally) a gamma
    '''

    __tablename__ = 'microscopy_fov_roi'

    id = sa.Column(sa.Integer, primary_key=True)
    fov_id = sa.Column(sa.Integer, sa.ForeignKey('microscopy_fov.id', ondelete='CASCADE'))

    # many ROIs to one FOV
    fov = sa.orm.relationship('MicroscopyFOV', back_populates='rois', uselist=False)

    # one ROI to many thumbnails
    thumbnails = sa.orm.relationship('MicroscopyFOVROIThumbnail', back_populates='roi')

    # kind of ROI: either 'corner' or 'annotated'
    kind = sa.Column(sa.String)

    # all ROI-specific metadata, including the ROI coordinates (position and shape),
    # the z-coordinate of the center of the cell layer,  and the min/max values
    # used to downsample the intensities from uint16 to uint8
    props = sa.Column(postgresql.JSONB)

    def get_thumbnail(self):
        return self.thumbnails[0] if self.thumbnails else None


class MicroscopyFOVThumbnail(Base, TimestampMixin):
    '''
    A base64-encoded RGB thumbnail of an FOV
    '''
    __tablename__ = 'microscopy_fov_thumbnail'
    id = sa.Column(sa.Integer, primary_key=True)

    fov_id = sa.Column(sa.Integer, sa.ForeignKey('microscopy_fov.id', ondelete='CASCADE'))
    fov = sa.orm.relationship('MicroscopyFOV', back_populates='thumbnails', uselist=False)

    # the size (in pixels) of the thumbnail image (which is assumed to be square)
    size = sa.Column(sa.Integer)

    # thumbnail itself as a base64-encoded PNG file
    data = sa.Column(sa.String)


class MicroscopyFOVROIThumbnail(Base, TimestampMixin):
    '''
    A base64-encoded RGB thumbnail of an ROI
    Unfortunately identical to MicroscopyFOVThumbnail,
    except for the foreign key to ROIs instead of FOVs
    '''
    __tablename__ = 'microscopy_fov_roi_thumbnail'
    id = sa.Column(sa.Integer, primary_key=True)

    roi_id = sa.Column(sa.Integer, sa.ForeignKey('microscopy_fov_roi.id', ondelete='CASCADE'))
    roi = sa.orm.relationship('MicroscopyFOVROI', back_populates='thumbnails', uselist=False)

    size = sa.Column(sa.Integer)
    data = sa.Column(sa.String)


class MicroscopyFOVAnnotation(Base, TimestampMixin):
    '''
    '''
    __tablename__ = 'microscopy_fov_annotation'
    id = sa.Column(sa.Integer, primary_key=True)

    # one annotation to one FOV
    fov_id = sa.Column(sa.Integer, sa.ForeignKey('microscopy_fov.id', ondelete='CASCADE'))
    fov = sa.orm.relationship('MicroscopyFOV', back_populates='annotation', uselist=False)

    # the row and column of the top-left corner of the user-selected ROI
    roi_position_top = sa.Column(sa.Integer)
    roi_position_left = sa.Column(sa.Integer)

    # the list of categories to which the FOV belongs (currently unused)
    categories = sa.Column(postgresql.JSONB)

    # the client-side timestamp, app state, etc
    client_metadata = sa.Column(postgresql.JSONB)
