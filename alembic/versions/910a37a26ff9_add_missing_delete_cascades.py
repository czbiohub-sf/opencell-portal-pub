"""add missing delete cascades

Revision ID: 910a37a26ff9
Revises: ca4d2bb29312
Create Date: 2021-03-23 17:07:44.422071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "910a37a26ff9"
down_revision = "ca4d2bb29312"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_cell_line_annotation_cell_line_id_cell_line",
        "cell_line_annotation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_cell_line_annotation_cell_line_id_cell_line"),
        "cell_line_annotation",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_cell_line_embedding_position_cell_line_id_cell_line",
        "cell_line_embedding_position",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_cell_line_embedding_position_cell_line_id_cell_line"),
        "cell_line_embedding_position",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_facs_dataset_cell_line_id_cell_line", "facs_dataset", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_facs_dataset_cell_line_id_cell_line"),
        "facs_dataset",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_mass_spec_cluster_heatmap_hit_id_mass_spec_hit",
        "mass_spec_cluster_heatmap",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_mass_spec_cluster_heatmap_hit_id_mass_spec_hit"),
        "mass_spec_cluster_heatmap",
        "mass_spec_hit",
        ["hit_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_mass_spec_hit_pulldown_id_mass_spec_pulldown", "mass_spec_hit", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_mass_spec_hit_pulldown_id_mass_spec_pulldown"),
        "mass_spec_hit",
        "mass_spec_pulldown",
        ["pulldown_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_mass_spec_pulldown_cell_line_id_cell_line", "mass_spec_pulldown", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_mass_spec_pulldown_cell_line_id_cell_line"),
        "mass_spec_pulldown",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_mass_spec_pulldown_network_pulldown_id_mass_spec_pulldown",
        "mass_spec_pulldown_network",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_mass_spec_pulldown_network_pulldown_id_mass_spec_pulldown"),
        "mass_spec_pulldown_network",
        "mass_spec_pulldown",
        ["pulldown_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_microscopy_fov_cell_line_id_cell_line", "microscopy_fov", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_microscopy_fov_cell_line_id_cell_line"),
        "microscopy_fov",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_sequencing_dataset_cell_line_id_cell_line", "sequencing_dataset", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_sequencing_dataset_cell_line_id_cell_line"),
        "sequencing_dataset",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_thumbnail_tile_position_cell_line_id_cell_line",
        "thumbnail_tile_position",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_thumbnail_tile_position_cell_line_id_cell_line"),
        "thumbnail_tile_position",
        "cell_line",
        ["cell_line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        op.f("fk_thumbnail_tile_position_cell_line_id_cell_line"),
        "thumbnail_tile_position",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_thumbnail_tile_position_cell_line_id_cell_line",
        "thumbnail_tile_position",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_sequencing_dataset_cell_line_id_cell_line"),
        "sequencing_dataset",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_sequencing_dataset_cell_line_id_cell_line",
        "sequencing_dataset",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_microscopy_fov_cell_line_id_cell_line"), "microscopy_fov", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_microscopy_fov_cell_line_id_cell_line",
        "microscopy_fov",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_mass_spec_pulldown_network_pulldown_id_mass_spec_pulldown"),
        "mass_spec_pulldown_network",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_mass_spec_pulldown_network_pulldown_id_mass_spec_pulldown",
        "mass_spec_pulldown_network",
        "mass_spec_pulldown",
        ["pulldown_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_mass_spec_pulldown_cell_line_id_cell_line"),
        "mass_spec_pulldown",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_mass_spec_pulldown_cell_line_id_cell_line",
        "mass_spec_pulldown",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_mass_spec_hit_pulldown_id_mass_spec_pulldown"),
        "mass_spec_hit",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_mass_spec_hit_pulldown_id_mass_spec_pulldown",
        "mass_spec_hit",
        "mass_spec_pulldown",
        ["pulldown_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_mass_spec_cluster_heatmap_hit_id_mass_spec_hit"),
        "mass_spec_cluster_heatmap",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_mass_spec_cluster_heatmap_hit_id_mass_spec_hit",
        "mass_spec_cluster_heatmap",
        "mass_spec_hit",
        ["hit_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_facs_dataset_cell_line_id_cell_line"), "facs_dataset", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_facs_dataset_cell_line_id_cell_line",
        "facs_dataset",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_cell_line_embedding_position_cell_line_id_cell_line"),
        "cell_line_embedding_position",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_cell_line_embedding_position_cell_line_id_cell_line",
        "cell_line_embedding_position",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_cell_line_annotation_cell_line_id_cell_line"),
        "cell_line_annotation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_cell_line_annotation_cell_line_id_cell_line",
        "cell_line_annotation",
        "cell_line",
        ["cell_line_id"],
        ["id"],
    )
    # ### end Alembic commands ###
