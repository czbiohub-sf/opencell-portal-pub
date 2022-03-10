"""drop the foreign key on uniprot_id in the abundance table

Revision ID: 90cfed289034
Revises: 1f51dcd6d06d
Create Date: 2022-02-24 08:58:11.918397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90cfed289034'
down_revision = '1f51dcd6d06d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        'fk_abundance_measurement_uniprot_id_uniprot_metadata',
        'abundance_measurement',
        type_='foreignkey',
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(
        'fk_abundance_measurement_uniprot_id_uniprot_metadata',
        'abundance_measurement',
        'uniprot_metadata',
        ['uniprot_id'],
        ['uniprot_id'],
        ondelete='CASCADE',
    )
    # ### end Alembic commands ###
