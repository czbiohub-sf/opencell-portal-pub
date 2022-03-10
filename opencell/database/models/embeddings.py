import sqlalchemy as sa
import sqlalchemy.orm

from opencell.database.models import Base

import logging
logger = logging.getLogger(__name__)


class CellLineEmbedding(Base):
    '''
    '''
    __tablename__ = 'cell_line_embedding'
    id = sa.Column(sa.Integer, primary_key=True)

    # human-readable name
    # for now, all of the embedding parameters (e.g., n_neighbors and min_dist for UMAPs)
    # that uniquely identify an embedding (modulo the grid_size) must be included in the name
    name = sa.Column(sa.String, nullable=False)

    # if grid size is null, the positions are assumed to be raw (un-gridded);
    # otherwise, the positions are the row and column indices of the grid
    grid_size = sa.Column(sa.Integer, nullable=True)

    positions = sa.orm.relationship('CellLineEmbeddingPosition', back_populates='embedding')

    __table_args__ = (sa.UniqueConstraint(name, grid_size),)


class CellLineEmbeddingPosition(Base):

    __tablename__ = 'cell_line_embedding_position'
    id = sa.Column(sa.Integer, primary_key=True)

    embedding_id = sa.Column(
        sa.Integer, sa.ForeignKey('cell_line_embedding.id', ondelete='CASCADE')
    )
    cell_line_id = sa.Column(sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'))
    position_x = sa.Column(sa.Float, nullable=False)
    position_y = sa.Column(sa.Float, nullable=False)

    embedding = sa.orm.relationship('CellLineEmbedding', back_populates='positions', uselist=False)


class ThumbnailTile(Base):
    '''
    A tiled array of best-fov thumbnails for each cell line
    '''
    __tablename__ = 'thumbnail_tile'
    id = sa.Column(sa.Integer, primary_key=True)

    # the filename of the tile itself
    # for now, the tile parameters (thumbnail size and shape, channel, etc)
    # are embedded in the filename, so that it must be unique
    filename = sa.Column(sa.String, nullable=False, unique=True)
    positions = sa.orm.relationship('ThumbnailTilePosition', back_populates='tile')


class ThumbnailTilePosition(Base):
    '''
    The position of a cell line's thumbnail in a tile
    '''
    __tablename__ = 'thumbnail_tile_position'
    id = sa.Column(sa.Integer, primary_key=True)

    tile_id = sa.Column(sa.Integer, sa.ForeignKey('thumbnail_tile.id', ondelete='CASCADE'))
    cell_line_id = sa.Column(sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'))

    tile_row = sa.Column(sa.Integer, nullable=False)
    tile_column = sa.Column(sa.Integer, nullable=False)

    tile = sa.orm.relationship('ThumbnailTile', back_populates='positions', uselist=False)
