"""add table for HGNC metadata

Revision ID: ca4d2bb29312
Revises: bedce04cf1d3
Create Date: 2021-01-26 19:22:51.550898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ca4d2bb29312"
down_revision = "bedce04cf1d3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "hgnc_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=True),
        sa.Column("prev_symbol", sa.String(), nullable=True),
        sa.Column("alias_symbol", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("prev_name", sa.String(), nullable=True),
        sa.Column("alias_name", sa.String(), nullable=True),
        sa.Column("hgnc_id", sa.String(), nullable=True),
        sa.Column("ensg_id", sa.String(), nullable=True),
        sa.Column(
            "date_created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hgnc_metadata")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("hgnc_metadata")
    # ### end Alembic commands ###
