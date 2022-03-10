import sqlalchemy as sa


class TimestampMixin:
    date_created = sa.Column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
