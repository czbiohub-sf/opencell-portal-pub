import re
import numpy as np
import pandas as pd

import sqlalchemy as sa
import sqlalchemy.orm
import sqlalchemy.ext.hybrid
import sqlalchemy.ext.declarative
from sqlalchemy.dialects import postgresql

from opencell.database import utils
from opencell.database.models import Base, enums, mixins

import logging
logger = logging.getLogger(__name__)


class CellLine(Base):
    '''
    All cell lines - progenitor, polyclonal, and monoclonal

    Progenitor cell lines are included here so that parent_id exists for both polyclonal lines
    that are direct descendents of a progenitor line and for monoclonal lines
    (that are, at least for now, descendents of a polyclonal line)

    '''

    __tablename__ = 'cell_line'

    id = sa.Column(sa.Integer, primary_key=True)

    # the type of cell line (progenitor, polyclonal, and monoconal)
    line_type = sa.Column(enums.cell_line_type_enum, nullable=False)

    # the sort count (identifies resorts; defined only for polyclonal lines)
    # NOTE: this column is troublesome; it is required to uniquely identify polyclonal lines,
    # but it also must be nullable (in anticipation of adding monoclonal lines),
    # so it is not possible to impose a unique constraint on
    # (progenitor_line_id, crispr_design_id, sort_count)
    sort_count = sa.Column(sa.Integer, nullable=True)

    # the sort date (for polyclonal and monoclonal lines)
    sort_date = sa.Column(sa.Date, nullable=True)

    # optional human-readable name
    name = sa.Column(sa.String, nullable=True)

    # optional human-readable notes
    notes = sa.Column(sa.String, nullable=True)

    # note that these foreign key ids are only null for progenitor cell lines
    parent_id = sa.Column(sa.Integer, sa.ForeignKey('cell_line.id'), nullable=True)
    crispr_design_id = sa.Column(sa.Integer, sa.ForeignKey('crispr_design.id'), nullable=True)

    parent = sa.orm.relationship('CellLine', remote_side=[id])
    children = sa.orm.relationship('CellLine')

    # the crispr design used to generate the cell line (if any)
    crispr_design = sa.orm.relationship(
        'CrisprDesign', back_populates='cell_lines', uselist=False
    )

    # one cell line to one manual annotation
    annotation = sa.orm.relationship(
        'CellLineAnnotation', back_populates='cell_line', uselist=False, passive_deletes='all'
    )

    # one cell line to one FACS dataset
    facs_dataset = sa.orm.relationship(
        'FACSDataset', back_populates='cell_line', uselist=False, passive_deletes='all'
    )

    # one cell line to one sequencing dataset
    sequencing_dataset = sa.orm.relationship(
        'SequencingDataset', back_populates='cell_line', uselist=False, passive_deletes='all'
    )

    # one cell_line to many FOVs
    fovs = sa.orm.relationship(
        'MicroscopyFOV', back_populates='cell_line', passive_deletes='all'
    )

    # one cell_line to many pulldowns
    pulldowns = sa.orm.relationship(
        'MassSpecPulldown', back_populates='cell_line', passive_deletes='all'
    )

    def __repr__(self):
        return (
            "<CellLine(id=%s, parent_id=%s, type='%s', target='%s')>"
            % (
                self.id,
                self.parent_id,
                self.line_type.value,
                self.crispr_design.target_name if self.crispr_design else None
            )
        )


    def get_best_pulldown(self):
        '''
        Get the 'good' pulldown
        This logic is necessary because there may be multiple pulldowns per cell line,
        but only ever one 'good' one whose hits should be displayed/analyzed
        '''
        if not self.pulldowns:
            return None

        # the manually-flagged 'good' pulldowns
        # (there should be only one of these, but we don't enforce this)
        candidate_pulldowns = [
            pulldown for pulldown in self.pulldowns if pulldown.manual_display_flag
        ]
        if not candidate_pulldowns:
            candidate_pulldowns = self.pulldowns
        return candidate_pulldowns[0]


    def get_top_scoring_fovs(self, ntop=None):
        '''
        Get the n highest-scoring FOVs
        '''
        scores = np.array([fov.get_score() for fov in self.fovs])

        # sort the FOVs by score
        mask = ~pd.isna(scores)
        scores[~mask] = -1
        inds = np.argsort(np.array(scores))[::-1]

        # drop inds without a score
        scores = [score for score in scores if score is not None]
        inds = inds[mask[inds]]

        # the n-highest-scoring FOVs
        ntop = len(inds) if ntop is None else ntop
        top_fovs = [self.fovs[ind] for ind in inds[:ntop]]
        return top_fovs


    def get_best_fov(self):
        '''
        Get the 'best' FOV
        For now, this is the first FOV that is manually annotated
        (using get_top_scoring_fovs is too slow)
        '''
        for fov in self.fovs:
            if fov.annotation:
                return fov
        return None


class PlateDesign(Base):
    '''
    Plate designs
    Keyed by a plate_id of the form 'P0001'
    '''
    __tablename__ = 'plate_design'

    # design_id is manually generated and of the form 'P0001'
    design_id = sa.Column(sa.String, primary_key=True)
    design_date = sa.Column(sa.Date)
    design_notes = sa.Column(sa.String)

    # one plate design to many crispr designs
    crispr_designs = sa.orm.relationship(
        'CrisprDesign',
        back_populates='plate_design',
        cascade='all, delete, delete-orphan'
    )

    def __repr__(self):
        return "<PlateDesign(design_id='%s')>" % self.design_id

    @sa.orm.validates('design_id')
    def validate_design_id(self, key, value):
        '''
        Validate and maybe format the plate design id
        '''
        return utils.format_plate_design_id(value)


class CrisprDesign(Base):
    '''
    Crispr designs

    This table combines three pieces of information:
        1) the crispr design itself (the guide and template sequences)
        2) the target metadata (gene name/family, ensembl ID, etc)
        3) the well in which the crispr design appears on the plate

    In principle, the crispr design and target metadata should have their own tables,
    since multiple crispr designs may (and sometimes do) share the same target,
    and the same design may appear in multiple wells and/or plate designs.

    In practice, however, this kind of overlap is rare enough that, for now,
    we take the shortcut of combining the design, target, and plate layout (well_id)
    into one table. Doing so also eliminates the complexity of
    1) determining how to uniquely identify targets, and
    2) checking whether each design and target is unique when inserting new plate designs.

    Furthermore, we do *not* require that the crispr design be unique
    (i.e., that the (protospacer_sequence, template_sequence) columns be unique),
    because there are several examples from plates 1-19 in which the same sequences
    are associated with distinct target names and metadata. Depending on how
    these apparent discrepancies are resolved, we can later consider placing a unique constraint
    on the guide and template sequences.

    Note that we use a serial primary key, but (well_id, plate_design_id) must be unique.

    '''
    __tablename__ = 'crispr_design'

    id = sa.Column(sa.Integer, primary_key=True)
    well_id = sa.Column(enums.well_id_enum, nullable=False)

    # gene/protein name
    target_name = sa.Column(sa.String, nullable=False)

    # gene family (optional)
    target_family = sa.Column(sa.String)

    # terminus at which the template was inserted
    # TODO: decide if NOT NULL is appropriate here
    # (currently, some designs from P0016 are null,
    # but only the 'jin' designs that should be ignored anyway)
    target_terminus = sa.Column(enums.terminus_type_enum, nullable=False)

    template_name = sa.Column(sa.String)
    template_notes = sa.Column(sa.String)
    template_sequence = sa.Column(sa.String, nullable=False)

    protospacer_name = sa.Column(sa.String)
    protospacer_notes = sa.Column(sa.String)
    protospacer_sequence = sa.Column(sa.String, nullable=False)

    # the plate_design on which this crispr_design appears
    plate_design_id = sa.Column(
        sa.String, sa.ForeignKey('plate_design.design_id'), nullable=False
    )

    # ensembl transcript id of the transcript tagged by the design
    # this is the fundamental identifier of the target tagged by the design
    # (though not the exact position or terminus of the tag)
    # note that this is unfortunately missing for some (early) designs,
    # for which uniprot_ids and ensg_ids must be retrieved using the target name
    enst_id = sa.Column(sa.String)

    # the ensg_id corresponding to the enst_id
    # (this is presumably redundant with enst_id but included to enable joins with hgnc_metadata)
    ensg_id = sa.Column(sa.String, sa.ForeignKey('hgnc_metadata.ensg_id'))

    hgnc_metadata = sa.orm.relationship('HGNCMetadata', uselist=False)

    # the uniprot_id corresponding to the enst_id
    # this cannot be a foreign key referencing uniprotkb_metadata.primary_uniprot_id,
    # because some crispr designs may target unreviewed proteins
    uniprot_id = sa.Column(sa.String)

    uniprotkb_metadata = sa.orm.relationship(
        'UniprotKBMetadata',
        foreign_keys=[uniprot_id],
        primaryjoin='CrisprDesign.uniprot_id == UniprotKBMetadata.primary_uniprot_id',
        uselist=False,
    )

    # many crispr_designs to one plate_design (96 wells per plate)
    plate_design = sa.orm.relationship(
        'PlateDesign', back_populates='crispr_designs', uselist=False
    )

    # one crispr_design to many cell lines
    cell_lines = sa.orm.relationship('CellLine', back_populates='crispr_design')

    # one crispr design to many mass spec protein groups
    protein_groups = sa.orm.relationship(
        'MassSpecProteinGroup',
        secondary='protein_group_crispr_design_association',
        back_populates='crispr_designs'
    )

    # the well_id must be unique in each plate design
    __table_args__ = (
        sa.UniqueConstraint(plate_design_id, well_id),
    )

    def __repr__(self):
        return (
            "<CrisprDesign(plate_id='%s', well_id=%s', target_name='%s')>" %
            (self.plate_design_id, self.well_id, self.target_name)
        )

    @sa.orm.validates('well_id')
    def format_well_id(self, key, value):
        '''
        Zero-pad well_ids ('A1' -> 'A01')
        '''
        return utils.format_well_id(value)

    @sa.orm.validates('target_terminus')
    def format_target_terminus(self, key, value):
        '''
        Coerce values beginning with 'int' to 'INTERNAL'
        '''
        if value is None:
            return value

        value = value.lower()
        if value.startswith('int'):
            logger.warning("Terminus type '%s' coerced to INTERNAL" % value)
            value = enums.TerminusTypeEnum.INTERNAL
        elif value.startswith('c'):
            if value != 'c':
                logger.warning("Terminus type '%s' coerced to C_TERMINUS" % value)
            value = enums.TerminusTypeEnum.C_TERMINUS
        elif value.startswith('n'):
            if value != 'n':
                logger.warning("Terminus type '%s' coerced to N_TERMINUS" % value)
            value = enums.TerminusTypeEnum.N_TERMINUS
        return value

    @sa.orm.validates('enst_id')
    def validate_enst_id(self, key, value):
        if value is not None and not re.match('^ENST[0-9]{11}$', value):
            raise ValueError('Invalid enst_id %s' % value)
        return value

    @sa.orm.validates('ensg_id')
    def validate_ensg_id(self, key, value):
        if value is not None and not re.match('^ENSG[0-9]{11}$', value):
            raise ValueError('Invalid ensg_id %s' % value)
        return value

    @sa.orm.validates('protospacer_sequence')
    def validate_protospacer_sequence(self, key, value):
        if not utils.is_sequence(value):
            raise ValueError('Invalid protospacer sequence %s' % value)
        return value

    @sa.orm.validates('template_sequence')
    def validate_template_sequence(self, key, value):
        if not utils.is_sequence(value):
            raise ValueError('Invalid template sequence %s' % value)
        return value

    def get_best_cell_line(self):
        '''
        Logic to choose the 'best' cell line when there is more than one
        '''
        if not self.cell_lines:
            return None

        for line in self.cell_lines:
            if line.sort_count > 1:
                return line

        for line in self.cell_lines:
            if line.get_best_pulldown():
                return line

        for line in self.cell_lines:
            if line.fovs:
                return line

        return self.cell_lines[0]


class UniprotMetadata(Base, mixins.TimestampMixin):
    '''
    Cached Uniprot metadata retrieved by querying UniprotKB and the Uniprot mapper API
    (see methods in uniprot_utils for details)
    '''
    __tablename__ = 'uniprot_metadata'
    uniprot_id = sa.Column(sa.String, primary_key=True)

    # these columns correspond to columns retrieved by UniprotKB queries
    protein_names = sa.Column(sa.String)
    protein_families = sa.Column(sa.String)
    gene_names = sa.Column(sa.String)
    annotation = sa.Column(sa.String)

    def get_primary_gene_name(self):
        return self.gene_names.split(' ')[0] if self.gene_names != 'NaN' else self.uniprot_id

    def __repr__(self):
        return (
            "<UniprotMetadata(uniprot_id='%s', gene_name='%s')>" %
            (self.uniprot_id, self.get_primary_gene_name())
        )


class UniprotKBMetadata(Base, mixins.TimestampMixin):
    '''
    Metadata for all human UniProtKB entries, parsed from a complete export of proteome UP000005640
    (see reference_datasets.populate_uniprotkb_metadata)
    '''
    __tablename__ = 'uniprotkb_metadata'

    # the 'natural' primary key for this table is the uniprotkb_id
    # (which the UniprotKB docs call the 'entry name'),
    # but the primary_uniprot_id is more convenient and is also unique,
    # at least within the human proteome from June 2021 (Uniprot proteome UP000005640)
    # (note that it is not clear whether it is unique by design,
    # so future releases of the human UniProtKB may require revisiting this)
    primary_uniprot_id = sa.Column(sa.String, primary_key=True)

    secondary_uniprot_ids = sa.Column(postgresql.ARRAY(sa.String))

    # the entry name and gene name (included only for sanity checks and human readability)
    entry_name = sa.Column(sa.String)
    gene_name = sa.Column(sa.String)

    # the functional annotation
    function_comment = sa.Column(sa.String)


class AbundanceMeasurement(Base, mixins.TimestampMixin):
    '''
    Measures of transcript and protein abundance in HEK293T
    Currently, this is transcript expression measured by RNAseq
    and protein abundance measured by whole-cell mass-spec
    '''
    __tablename__ = 'abundance_measurement'

    uniprot_id = sa.Column(sa.String, primary_key=True)

    # gene name (just for human readability and sanity checks)
    gene_name = sa.Column(sa.String)

    # gene expression from RNA-seq (in transcripts per million)
    # (technically should be keyed by enst_id, not uniprot_id)
    measured_transcript_expression = sa.Column(sa.Float)

    # the cellular protein concentration estimated from mass spec intensities
    # (as a nanomolar concentration)
    measured_protein_concentration = sa.Column(sa.Float)

    # the cellular protein concentration imputed from RNA-seq expression level
    # (as a nanomolar concentration)
    imputed_protein_concentration = sa.Column(sa.Float)

    @staticmethod
    def calc_protein_copy_number(concentration):
        '''
        Calculate the protein copy number per cell from a nanomolar concentration
        (which is either measured or imputed)
        '''
        # the number of copies per cell per nanomolar (from Marco)
        # (this is derived from the volume used to calculate protein concentration from copy number)
        copies_per_cell_per_nanomolar = 602

        if pd.isna(concentration):
            return None
        return concentration * copies_per_cell_per_nanomolar


class HGNCMetadata(Base, mixins.TimestampMixin):
    '''
    The HGNC entries for all protein-coding genes from the HGNC,
    excluding non-primary ensg_ids (i.e., those associated with alternative sequences)
    (see reference_datasets.load_hgnc_dataset for details)

    This table corresponds to the reference set of primary ensg_ids to which other entities
    (e.g., crispr designs and protein groups) are later associated.

    Note: the 'symbol' columns are the gene names
    and the 'name' columns correspond to what UniProt calls protein names
    '''
    __tablename__ = 'hgnc_metadata'

    # the 'natural' primary key for this table is the hgnc_id, but we use the ensg_id here
    # to make it explicit that this table corresponds to the set of reference ensg_ids
    # to which crispr designs and protein groups are mapped
    # (nb in the protein-coding HGNC dataset, the ensg_id - hgnc_id map is indeed 1-to-1)
    ensg_id = sa.Column(sa.String, primary_key=True)
    hgnc_id = sa.Column(sa.String, unique=True)

    symbol = sa.Column(sa.String)
    prev_symbol = sa.Column(sa.String)
    alias_symbol = sa.Column(sa.String)

    name = sa.Column(sa.String)
    prev_name = sa.Column(sa.String)
    alias_name = sa.Column(sa.String)

    # the secondary join condition must be specified because there is no foreign-key constraint
    # between the uniprot_ids in the association table
    # and the primary_uniprot_ids in the uniprotkb_metadata table
    uniprotkb_metadata = sa.orm.relationship(
        'UniprotKBMetadata',
        secondary='ensembl_uniprot_association',
        secondaryjoin='EnsemblUniprotAssociation.uniprot_id == UniprotKBMetadata.primary_uniprot_id',
        uselist=True,
        viewonly=True
    )

    abundance_measurements = sa.orm.relationship(
        'AbundanceMeasurement',
        secondary='ensembl_uniprot_association',
        secondaryjoin='EnsemblUniprotAssociation.uniprot_id == AbundanceMeasurement.uniprot_id',
        uselist=True,
        viewonly=True
    )


class EnsemblUniprotAssociation(Base):
    '''
    Association between the 'primary' Ensembl gene ids (ensg_ids) in the hgnc_metadata table
    and their UniProt IDs, derived from an ensembl mapping export
    Note: this map is often one-to-one, but can be one-to-many, many-to-one, or many-to-many
    (See reference_datasets.generate_primary_ensg_to_uniprot_map for details)
    '''
    __tablename__ = 'ensembl_uniprot_association'
    ensg_id = sa.Column(
        sa.String, sa.ForeignKey('hgnc_metadata.ensg_id'), primary_key=True, index=True
    )
    uniprot_id = sa.Column(sa.String, primary_key=True, index=True)


class FACSDataset(Base):
    '''
    A single FACS dataset, consisting of
        1) the sample and fitted reference histograms
        2) various extracted properties (GFP-positive area, median/max intensities, etc)

    Each of these datasets must correspond to a single cell line,
    and there should be only one dataset per cell line, though this may change
    and is currently not enforced.

    In practice, and possibly also in principle, FACS datasets should exist
    only for polyclonal lines, though this is not currently enforced.

    For now, we use the cell_line_id as the primary key.

    TODO: add columns for date_generated, git_commit, and sample/control dirpaths

    '''

    __tablename__ = 'facs_dataset'

    cell_line_id = sa.Column(
        sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'), primary_key=True
    )

    # histograms
    histograms = sa.Column(postgresql.JSONB)

    # extracted properties (area, median intensity, etc)
    scalars = sa.Column(postgresql.JSONB)

    # one dataset to one cell_line
    cell_line = sa.orm.relationship('CellLine', back_populates='facs_dataset', uselist=False)


    def simplify_histograms(self):
        '''
        Downsample and discretize the histograms
        This is intended to reduce the payload size when the histograms
        will only be used to generate thumbnail/sparkline-like plots

        Note that the scaling, rounding, and 2x-subsampling were empirically determined
        as the most extreme downsampling that still yields satisfactory thumbnail-sized plots
        ('thumbnail-sized' means plots on the order of 100px wide)
        '''

        if self.histograms is None:
            return None
        histograms = self.histograms.copy()

        # x-axis values can be safely rounded to ints
        histograms['x'] = [int(x) for x in histograms['x']]

        # y-axis values (densities) must be scaled before rounding
        scale_factor = 1e6
        for key in 'y_sample', 'y_ref_fitted':
            histograms[key] = [int(y*scale_factor) for y in histograms[key]]

        # finally, downsample by 2x
        for key in histograms.keys():
            histograms[key] = histograms[key][::2]
        return histograms


class SequencingDataset(Base):
    '''
    Some processed results from the sequencing dataset for a single polyclonal cell line
    '''

    __tablename__ = 'sequencing_dataset'

    cell_line_id = sa.Column(
        sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'), primary_key=True
    )

    # extracted properties (percent HDR among all alleles and modified alleles)
    scalars = sa.Column(postgresql.JSONB)

    # one dataset to one cell_line
    cell_line = sa.orm.relationship(
        'CellLine', back_populates='sequencing_dataset', uselist=False
    )


class CellLineAnnotation(Base, mixins.TimestampMixin):
    '''
    '''

    __tablename__ = 'cell_line_annotation'

    id = sa.Column(sa.Integer, primary_key=True)

    # one anotation to one cell_line
    cell_line_id = sa.Column(sa.Integer, sa.ForeignKey('cell_line.id', ondelete='CASCADE'))
    cell_line = sa.orm.relationship('CellLine', back_populates='annotation', uselist=False)

    # free-form comments
    comment = sa.Column(sa.String)

    # the list of categories to which the cell line belongs
    categories = sa.Column(postgresql.JSONB)

    # the client-side timestamp, app state, etc
    client_metadata = sa.Column(postgresql.JSONB)
