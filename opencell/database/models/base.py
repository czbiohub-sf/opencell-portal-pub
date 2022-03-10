import enum
import pandas as pd
import sqlalchemy as sa
import sqlalchemy.ext.declarative

# constraint naming conventions
# see https://alembic.sqlalchemy.org/en/latest/naming.html
metadata = sa.MetaData(
    naming_convention={
        "ix": "idx_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class BaseMixin:

    # TODO: decide whether we need to keep `extend_existing` here
    # (originally for autoreloading during development)
    __table_args__ = {'extend_existing': True}

    def as_dict(self):
        '''
        Rudimentary object serialization, intended to facilitate
        the construction of JSON-able objects
        '''
        d = {}
        for column in self.__table__.columns:  # pylint: disable=no-member
            value = getattr(self, column.name)
            if isinstance(value, enum.Enum):
                value = value.value
            try:
                if pd.isna(value):
                    value = None
            except ValueError:
                pass
            d[column.name] = value
        return d


Base = sa.ext.declarative.declarative_base(cls=BaseMixin, metadata=metadata)
