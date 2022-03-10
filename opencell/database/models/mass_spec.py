import logging
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from opencell.database import utils, models
from opencell.database.models import Base
from opencell.database.models.mixins import TimestampMixin

logger = logging.getLogger(__name__)


class MassSpecPulldownPlate(Base, TimestampMixin):
    '''
    A mass spec plate prepped by the ML Group

    Note that these plates consist of sets of pulldowns performed on some subset of cell lines,
    and are totally unrelated to the plates of crispr designs in the plate_design table.
    '''
    __tablename__ = 'mass_spec_pulldown_plate'

    # format is of the form 'CZBMPI_{plate_num:04d}'
    id = sa.Column(sa.String, primary_key=True)

    # link to the google sheet design of the plate mapping out pulldown
    # target locations by well
    plate_design_link = sa.Column(sa.String)

    # Description of the pulldown (whether it is a repeat or subset, etc)
    description = sa.Column(sa.String)

    # one plate to many pulldowns
    pulldowns = sa.orm.relationship('MassSpecPulldown', back_populates='pulldown_plate')


class MassSpecPulldown(Base, TimestampMixin):
    '''
    A pulldown performed on a cell_line and analyzed by ms-ms
    (in which the GFP-tagged target was used as the 'bait')
    '''

    __tablename__ = 'mass_spec_pulldown'
    id = sa.Column(sa.Integer, primary_key=True)
    cell_line_id = sa.Column(sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'))
    pulldown_plate_id = sa.Column(
        sa.String, sa.ForeignKey('mass_spec_pulldown_plate.id'), nullable=False
    )

    # 1% fdr offset and curvature calculated for this pulldown
    fdr_1_offset = sa.Column(sa.Float)
    fdr_1_curvature = sa.Column(sa.Float)

    # 5% fdr offset and curvature calculated for this pulldown
    fdr_5_offset = sa.Column(sa.Float)
    fdr_5_curvature = sa.Column(sa.Float)

    # manual flag for the pulldown to be shown in the OC if there are
    # multiple pulldowns per crisprdesign. Boolean variable:
    # pulldown flag with 1 should be displayed, 0 should not be displayed
    manual_display_flag = sa.Column(sa.Boolean)

    # one pulldown to one cell line
    cell_line = sa.orm.relationship('CellLine', back_populates='pulldowns', uselist=False)

    # one pulldown to many hits
    hits = sa.orm.relationship('MassSpecHit', back_populates='pulldown', passive_deletes='all')

    # many pulldowns to one pulldown_plate
    pulldown_plate = sa.orm.relationship(
        'MassSpecPulldownPlate', back_populates='pulldowns', uselist=False
    )

    # the cached cytoscape network for the pulldown
    network = sa.orm.relationship(
        'MassSpecPulldownNetwork', back_populates='pulldown', uselist=False, passive_deletes='all'
    )

    def get_target_name(self):
        '''Convenience method to get target_name for each pulldown'''
        return self.cell_line.crispr_design.target_name


    def get_significant_hits(self, protein_group_ids=None, eagerload=True):
        '''
        Retrieve the significant hits and optionally eager-load their protein groups
        and the protein groups' crispr designs and uniprot metadata
        '''
        query = (
            sa.orm.object_session(self).query(MassSpecHit)
            .options(sa.orm.joinedload(MassSpecHit.protein_group, innerjoin=True))
            .filter(MassSpecHit.pulldown_id == self.id)
            .filter(sa.or_(
                MassSpecHit.is_minor_hit == True,  # noqa
                MassSpecHit.is_significant_hit == True  # noqa
            ))
        )
        if protein_group_ids:
            query = query.filter(MassSpecHit.protein_group_id.in_(protein_group_ids))

        if eagerload:
            query = query.options(
                sa.orm.joinedload(MassSpecHit.protein_group, innerjoin=True)
                .joinedload(MassSpecProteinGroup.crispr_designs),
                sa.orm.joinedload(MassSpecHit.protein_group, innerjoin=True)
                .joinedload(MassSpecProteinGroup.hgnc_metadata),
            )
        significant_hits = query.all()
        return significant_hits


    def get_bait_hit(self, only_one=False):
        '''
        Get the hit(s) that corresponds to the pulldown's target/bait
        Returns none if the bait does not appear among the hits
        '''
        bait_hits = (
            sa.orm.object_session(self).query(MassSpecHit)
            .join(MassSpecProteinGroup)
            .join(ProteinGroupCrisprDesignAssociation)
            .join(models.CrisprDesign)
            .filter(MassSpecHit.pulldown_id == self.id)
            .filter(sa.or_(
                MassSpecHit.is_minor_hit == True,  # noqa
                MassSpecHit.is_significant_hit == True  # noqa
            ))
            .filter(models.CrisprDesign.id == self.cell_line.crispr_design.id)
            .all()
        )
        if not bait_hits:
            return None
        if only_one:
            # return the hit with the greatest enrichment
            bait_hits = sorted(bait_hits, key=lambda hit: -hit.enrichment)
            return bait_hits[0]
        return bait_hits


    def get_interacting_pulldowns(self):
        '''
        Get the 'interacting pulldowns' in which one or more of the protein groups
        associated with the pulldown's target appears as a significant hit

        TODO: consider using only the protein_group of the bait hit to do the filtering
        '''
        interacting_pulldowns = (
            sa.orm.object_session(self).query(MassSpecPulldown).join(MassSpecHit)
            .filter(sa.or_(
                MassSpecPulldown.manual_display_flag == None,  # noqa
                MassSpecPulldown.manual_display_flag == True  # noqa
            ))
            .filter(MassSpecPulldown.id != self.id)
            .filter(
                MassSpecHit.protein_group_id.in_(
                    [group.id for group in self.cell_line.crispr_design.protein_groups]
                )
            )
            .filter(sa.or_(
                MassSpecHit.is_minor_hit == True,  # noqa
                MassSpecHit.is_significant_hit == True  # noqa
            ))
            .all()
        )
        return interacting_pulldowns


    def __repr__(self):
        return (
            "<MassSpecPulldown(id=%s, pulldown_plate_id=%s, target_name=%s)>"
            % (self.id, self.pulldown_plate_id, self.get_target_name())
        )


class MassSpecProteinGroup(Base, TimestampMixin):
    '''
    A protein group identified by msms in experiments
    '''

    __tablename__ = 'mass_spec_protein_group'

    # id is a hash of unique set of peptide Uniprot ids that compose the protein group
    id = sa.Column(sa.String, primary_key=True)

    # a list of all uniprot gene names mapped to the protein group
    gene_names = sa.Column(postgresql.ARRAY(sa.String))

    # a list of all peptide Uniprot ids (including isoforms)
    uniprot_ids = sa.Column(postgresql.ARRAY(sa.String))

    # an optional manually-defined gene name (for the opencell frontend)
    # This is needed because sometimes the protein group's unique uniprot gene names
    # consist of multiple isoforms and homologs of the 'same' protein
    # the manual_gene_name is a human-defined simplified nomenclature for such cases
    manual_gene_name = sa.Column(sa.String, nullable=True)

    # one protein_group to many hits
    hits = sa.orm.relationship('MassSpecHit', back_populates='protein_group')

    # one protein group to (possibly) more than one crispr design
    crispr_designs = sa.orm.relationship(
        'CrisprDesign',
        secondary='protein_group_crispr_design_association',
        back_populates='protein_groups'
    )

    # one protein group to multiple uniprot metadata rows
    hgnc_metadata = sa.orm.relationship(
        'HGNCMetadata',
        secondary='protein_group_ensembl_association'
    )

    def get_pulldowns(self):
        '''
        Get the pulldowns in which the protein group appears as a significant hit
        '''
        pulldowns = (
            sa.orm.object_session(self).query(MassSpecPulldown)
            .join(MassSpecHit)
            .join(MassSpecProteinGroup)
            .filter(MassSpecProteinGroup.id == self.id)
            .filter(sa.or_(
                MassSpecPulldown.manual_display_flag == None,  # noqa
                MassSpecPulldown.manual_display_flag == True  # noqa
            ))
            .filter(sa.or_(
                MassSpecHit.is_minor_hit == True,  # noqa
                MassSpecHit.is_significant_hit == True  # noqa
            ))
            .all()
        )
        return pulldowns

    def __repr__(self):
        return "<MassSpecProteinGroup(gene_names=[%s])>" % (', '.join(self.gene_names))


class MassSpecHit(Base, TimestampMixin):
    '''
    A hit is a protein group identified in a pulldown and associated with a mass-spec intensity.
    Here the table is populated with the pre-computed enrichment and p-value
    of the hit compared to a base distribution.
    '''

    __tablename__ = 'mass_spec_hit'
    id = sa.Column(sa.Integer, primary_key=True)

    # hashed string of sorted Uniprot peptide IDs that compose the protein group
    protein_group_id = sa.Column(
        sa.String, sa.ForeignKey('mass_spec_protein_group.id'), index=True
    )

    # many hits to one pulldown
    pulldown_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('mass_spec_pulldown.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # p-value of the hit's MS intensity
    pval = sa.Column(sa.Float, nullable=False)

    # enrichment of the hit's MS intensity
    enrichment = sa.Column(sa.Float, nullable=False)

    # boolean specifying whether the hit is significant based on FDR threshold
    is_significant_hit = sa.Column(sa.Boolean, index=True)

    # boolean specifying whether the hit is significant based on a lower FDR threshold
    is_minor_hit = sa.Column(sa.Boolean, index=True)

    # interaction stoichiometry of the prey relative to the target
    interaction_stoich = sa.Column(sa.Float)

    # abundance stoichiometry of the prey relative to the garget
    abundance_stoich = sa.Column(sa.Float)

    # many hits to one pulldown
    pulldown = sa.orm.relationship('MassSpecPulldown', back_populates='hits', uselist=False)

    # one hit to one protein_group
    protein_group = sa.orm.relationship(
        'MassSpecProteinGroup', back_populates='hits', uselist=False
    )

    # A hit needs to have a unique set of target (pulldown) and the prey (protein_group)
    __table_args__ = (sa.UniqueConstraint(pulldown_id, protein_group_id),)

    def __repr__(self):
        return (
            "<MassSpecHit(bait=%s, pval=%0.2f, enrichment=%0.2f, gene_names=[%s])>"
            % (
                self.pulldown.get_target_name(),
                float(self.pval),
                float(self.enrichment),
                ', '.join(self.protein_group.gene_names)
            )
        )


class MassSpecClusterHeatmap(Base):
    """
    This table contains hard-coded cluster memberships of interactions as well as
    coordinates for hierarchical layout of cluster heatmap.
    Used by resources.PulldownClusters and to determine cluster memberships
    during target network construction in resources.PulldownNetwork
    """
    __tablename__ = 'mass_spec_cluster_heatmap'
    id = sa.Column(sa.Integer, primary_key=True)

    # cluster, subcluster, and core complex ids
    cluster_id = sa.Column(sa.Integer, nullable=False)
    subcluster_id = sa.Column(sa.Integer, nullable=True)
    core_complex_id = sa.Column(sa.Integer, nullable=True)

    # the hit that the heatmap coordinate refers to
    hit_id = sa.Column(
        sa.Integer, sa.ForeignKey('mass_spec_hit.id', ondelete='CASCADE'), nullable=False
    )

    # row and column index of the heat map
    row_index = sa.Column(sa.Integer, nullable=False)
    col_index = sa.Column(sa.Integer, nullable=False)

    # clustering analysis identifier describing the cluster pipeline used
    analysis_type = sa.Column(sa.String, nullable=False)

    # many cluster rows to one mass spec hit
    hit = sa.orm.relationship('MassSpecHit', uselist=False)

    # The row and col indexes should be unique within a cluster
    __table_args__ = (sa.UniqueConstraint(cluster_id, row_index, col_index, analysis_type),)


class MassSpecPulldownNetwork(Base, TimestampMixin):
    '''
    Cached cytoscape network and layout (generated by cytoscapejs)
    '''
    __tablename__ = 'mass_spec_pulldown_network'

    id = sa.Column(sa.Integer, primary_key=True)

    # one network to one pulldown
    pulldown_id = sa.Column(sa.Integer, sa.ForeignKey('mass_spec_pulldown.id', ondelete='CASCADE'))
    pulldown = sa.orm.relationship(
        'MassSpecPulldown', back_populates='network', uselist=False
    )

    # this is currently unused
    last_modified = sa.Column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())

    # the JSON dump from cy.json()
    cytoscape_json = sa.Column(postgresql.JSONB)

    # the client-side timestamp, app state, etc
    client_metadata = sa.Column(postgresql.JSONB)


class ProteinGroupEnsemblAssociation(Base):
    '''
    Association between the primary ensg_ids defined in the hgnc_metadata table
    and *significant* protein groups (those associated with at least one significant hit)

    Note: in general, this map is many-to-many (but one ENSG ID to many PGs should be rare)
    '''
    __tablename__ = 'protein_group_ensembl_association'
    ensg_id = sa.Column(
        sa.String, sa.ForeignKey('hgnc_metadata.ensg_id'), primary_key=True, index=True
    )
    protein_group_id = sa.Column(
        sa.String, sa.ForeignKey('mass_spec_protein_group.id'), primary_key=True, index=True
    )


class ProteinGroupCrisprDesignAssociation(Base):
    '''
    Association between 'significant' protein groups
    (defined as those in protein_group_ensembl_association)
    and all crispr_designs (including crispr_designs for unpublished targets)
    '''
    __tablename__ = 'protein_group_crispr_design_association'
    crispr_design_id = sa.Column(
        sa.Integer, sa.ForeignKey('crispr_design.id'), primary_key=True, index=True
    )
    protein_group_id = sa.Column(
        sa.String, sa.ForeignKey('mass_spec_protein_group.id'), primary_key=True, index=True
    )
