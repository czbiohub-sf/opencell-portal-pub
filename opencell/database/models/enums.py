import enum
import sqlalchemy as sa
from opencell.database import constants


class TerminusTypeEnum(enum.Enum):
    N_TERMINUS = 'N_TERMINUS'
    C_TERMINUS = 'C_TERMINUS'
    INTERNAL = 'INTERNAL'


class CellLineTypeEnum(enum.Enum):
    PROGENITOR = 'PROGENITOR'
    POLYCLONAL = 'POLYCLONAL'
    MONOCLONAL = 'MONOCLONAL'


terminus_type_enum = sa.Enum(TerminusTypeEnum, name='terminus_type_enum')
cell_line_type_enum = sa.Enum(CellLineTypeEnum, name='cell_line_type_enum')
well_id_enum = sa.Enum(*constants.DATABASE_WELL_IDS, name='well_id_type_enum')
