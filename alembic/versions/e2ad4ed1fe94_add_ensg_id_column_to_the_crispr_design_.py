"""add ensg_id column to the crispr_design table

Revision ID: e2ad4ed1fe94
Revises: bed48aaf3414
Create Date: 2022-02-17 09:17:07.995565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2ad4ed1fe94'
down_revision = 'bed48aaf3414'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('crispr_design', sa.Column('ensg_id', sa.String(), nullable=True))
    op.alter_column('crispr_design', 'transcript_id', new_column_name='enst_id')
    op.drop_column('crispr_design', 'terminus_notes')
    op.drop_column('crispr_design', 'transcript_notes')
    # ### end Alembic commands ###


def downgrade():
    op.add_column(
        'crispr_design',
        sa.Column('transcript_notes', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'crispr_design',
        sa.Column('terminus_notes', sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.alter_column('crispr_design', 'enst_id', new_column_name='transcript_id')
    op.drop_column('crispr_design', 'ensg_id')

    # ### end Alembic commands ###
