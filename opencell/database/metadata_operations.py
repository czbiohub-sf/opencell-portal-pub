import logging
import pandas as pd
import sqlalchemy as sa

from opencell.database import constants, models, utils, file_utils

logger = logging.getLogger(__name__)


def get_or_create_progenitor_cell_line(session, name, notes=None, create=False):
    '''
    Get or create a progenitor cell line by manual entry

    'Progenitor' cell lines are strictly those used for electroporations;
    they are therefore the root nodes in the self-referential cell_line table
    (which contains predominately polyclonal and monoclonal lines).

    The use of a human-readable name here is just for convenience and is intended
    to facilitate the creation/retrieval of the progenitor cell lines used for electroporation
    (of which we can assume there will be very few).

    Parameters
    ----------
    name : required human-readable and unique name for the cell_line
    notes : optional human-readable notes about the cell line
    create : whether to create a cell line with the given name if one does not already exist

    Returns
    -------
    A CellLine instance corresponding to the progenitor cell line

    '''
    # check whether the progenitor cell line already exists
    cell_line = (
        session.query(models.CellLine)
        .filter(models.CellLine.name == name)
        .one_or_none()
    )
    if cell_line is not None and create:
        logger.warning("A cell line with the name '%s' already exists" % name)

    elif cell_line is None and create:
        logger.info("Creating progenitor cell line with name '%s'" % name)
        cell_line = models.CellLine(name=name, notes=notes, line_type='PROGENITOR')
        utils.add_and_commit(session, cell_line)

    elif cell_line is None:
        logger.warning("A progenitor cell line with name '%s' does not exist" % name)

    return cell_line


def get_or_create_plate_design(session, design_id, date=None, notes=None, create=False):
    '''
    Get or create a new plate design (nb date and notes are optional)
    '''
    plate_design = (
        session.query(models.PlateDesign)
        .filter(models.PlateDesign.design_id == design_id)
        .one_or_none()
    )
    if create and plate_design is not None:
        logger.warning('Plate design %s already exists' % design_id)
    elif plate_design is None:
        if create:
            plate_design = models.PlateDesign(
                design_id=design_id, design_date=date, design_notes=notes
            )
            utils.add_and_commit(session, plate_design)
        else:
            logger.warning('plate_design %s does not exist and will not be created' % design_id)
            return None

    return plate_design


def create_crispr_designs(session, plate_design, library_snapshot, drop_existing=False):
    '''
    Insert all crispr designs for a given plate design,
    using a snapshot of the library spreadsheet.

    Parameters
    ----------
    session : sqlalchemy session
    plate_design : PlateDesign instance corresponding to the plate
        whose crispr designs are to be inserted
    library_snapshot : a snapshot of the library spreadsheet as a pandas dataframe
    drop_existing : whether to drop any existing crispr designs linked to this plate
    '''
    # crop the library to the current plate
    designs = library_snapshot.loc[
        library_snapshot.plate_id == plate_design.design_id
    ].copy()

    # discard the plate_id
    designs.drop(labels=['plate_id'], axis=1, inplace=True)

    # coerce nan to None (sqlalchemy doesn't coerce np.nan to NULL)
    designs.replace({pd.np.nan: None}, inplace=True)

    logger.info(
        'Inserting %s new crispr designs for plate %s' % (designs.shape[0], plate_design.design_id)
    )
    # check that we have the expected number of designs/wells to insert
    if designs.shape[0] != len(constants.DATABASE_WELL_IDS):
        logger.warning('Found %s crispr designs to insert, but 96 are expected' % designs.shape[0])

    # drop the negative (empty) controls
    designs = designs.loc[designs.target_name != 'empty_control']

    # delete all existing crispr designs
    if drop_existing:
        utils.delete_and_commit(session, plate_design.crispr_designs)

    # create the crispr designs
    crispr_designs = [
        models.CrisprDesign(plate_design=plate_design, **design)
        for _, design in designs.iterrows()
    ]
    utils.add_and_commit(session, crispr_designs)


def create_polyclonal_lines(session, progenitor_cell_line, plate_design, date):
    '''
    Create the initial polyclonal lines generated by electroporating a single plate

    Parameters
    ----------
    progenitor_cell_line : the CellLine instance corresponding to the electroporated cell line
    plate_design : the PlateDesign instance corresponding to the electroporated plate
    date : the date, as a string, of the electroporation
            (required to disambiguate electroporations of the same plate)
    '''

    line_type = 'POLYCLONAL'

    # sort count is always `1` for the initial sort after electroporation
    sort_count = 1

    for crispr_design in plate_design.crispr_designs:

        # check for an existing polyclonal line associated with this crispr design
        # (this is necessary because there is no unique constraint on
        # (progenitor_line_id, crispr_design_id, sort_count))
        existing_line = (
            session.query(models.CellLine)
            .filter(models.CellLine.parent_id == progenitor_cell_line.id)
            .filter(models.CellLine.line_type == line_type)
            .filter(models.CellLine.crispr_design_id == crispr_design.id)
            .filter(models.CellLine.sort_count == sort_count)
            .one_or_none()
        )
        if existing_line:
            logger.warning(
                'A polyclonal cell line already exists for (%s, %s)'
                % (plate_design.design_id, crispr_design.well_id)
            )
            continue

        cell_line = models.CellLine(
            parent_id=progenitor_cell_line.id,
            crispr_design=crispr_design,
            line_type=line_type,
            sort_count=sort_count,
            sort_date=date
        )
        utils.add_and_commit(session, cell_line)


def get_lines_by_annotation(engine, annotation):
    '''
    Get the ids of all cell lines with a particular manual annotation category
    '''
    result = pd.read_sql(
        '''
        select cell_line_id from(
            select cell_line_id, json_array_elements_text(categories::json) as cat
            from cell_line_annotation
        ) tmp
        where cat = %(annotation)s
        ''',
        engine,
        params=dict(annotation=annotation)
    )
    return result.cell_line_id.tolist()


def insert_plate_design(session, plate_id, library_snapshot_filepath):
    '''
    Insert a new plate design and its crispr designs
    This method is intended to update an existing opencell database when a new plate is created
    '''
    # the 'library snapshot' is the 'da list' google sheet of all crispr designs
    library_snapshot = file_utils.load_library_snapshot(library_snapshot_filepath)

    logger.info('Inserting crispr designs for plate %s' % plate_id)
    plate_design = get_or_create_plate_design(session, plate_id, create=True)
    create_crispr_designs(
        session, plate_design, library_snapshot, drop_existing=False
    )


def insert_electroporation(session, plate_id, electroporation_date):
    '''
    Create the polyclonal lines generated by electroporating and sorting a single plate
    '''
    logger.info('Creating polyclonal lines for plate %s' % plate_id)
    progenitor_line = get_or_create_progenitor_cell_line(session, constants.PARENTAL_LINE_NAME)
    plate_design = get_or_create_plate_design(session, plate_id)
    create_polyclonal_lines(
        session,
        progenitor_line,
        plate_design,
        date=electroporation_date,
    )


def insert_resorted_lines(session, resorts_snapshot):
    '''
    Insert once-resorted polyclonal cell lines from a google sheet snapshot
    (that is, lines with sort_count = 2)

    resorts_snapshot : snapshot of the google sheet of resorted lines,
        with columns 'plate_id', 'pipeline_well_id', and 'resorting_date'
    '''
    resorts_snapshot.dropna(how='any', axis=0, inplace=True)

    # zero-pad the well_ids
    resorts_snapshot['pipeline_well_id'] = resorts_snapshot.pipeline_well_id.apply(
        utils.format_well_id
    )
    for ind, row in resorts_snapshot.iterrows():
        logger.info('Inserting resorted cell line for (%s, %s)' % (row.plate_id, row.pipeline_well_id))
        line_operations = PolyclonalLineOperations.from_plate_well(
            session, row.plate_id, row.pipeline_well_id, sort_count=1
        )
        if not line_operations:
            continue
        line_operations.insert_resorted_line(
            session, sort_count=2, sort_date=row.resorting_date
        )


class PolyclonalLineOperations:
    '''
    Methods to retrieve and insert datasets that are associated with a single polyclonal line
    '''

    def __init__(self, line):
        self.line = line


    @classmethod
    def from_line_id(cls, session, line_id, eager=False):
        '''
        '''
        query = session.query(models.CellLine)
        if eager:
            query = query.options(
                sa.orm.joinedload(models.CellLine.fovs, innerjoin=True)
                .joinedload(models.MicroscopyFOV.results, innerjoin=True)
            )
        return cls(query.get(line_id))


    @classmethod
    def from_plate_well(cls, session, design_id, well_id, sort_count):
        '''
        Retrieve a polyclonal cell line given a plate_id, a well_id, and a sort_count

        Parameters
        ----------
        design_id : the plate design id (in the form 'P0001')
        well_id : the zero-padded well_id (in the form 'A01')
        sort_count : integer that distinguishes between the 'original' line and subsequent resorts
            1 for the original polyclonal line
            2 for the resorted descendent (if any)
            3 for the resort of the resort (if any)
        '''
        lines = (
            session.query(models.CellLine)
            .join(models.CrisprDesign)
            .filter(models.CrisprDesign.plate_design_id == design_id)
            .filter(models.CrisprDesign.well_id == well_id)
            .filter(models.CellLine.sort_count == sort_count)
            .all()
        )

        if not lines:
            logger.warning(
                "No cell line exists with a sort_count of %s for well %s of plate %s"
                % (sort_count, well_id, design_id)
            )
            return None

        if len(lines) > 1:
            logger.warning(
                "More than one cell line exists with a sort_count of %s for well %s of plate %s"
                % (sort_count, well_id, design_id)
            )

        return cls(lines[0])


    @classmethod
    def from_target_name(cls, session, target_name):
        '''
        Retrieve a cell line given a target_name

        Note: if there is more than one cell line for the target_name,
        then the PolyClonalLineOperations class is instantiated using the first such cell_line
        '''
        lines = (
            session.query(models.CellLine)
            .join(models.CrisprDesign)
            .filter(sa.func.lower(models.CrisprDesign.target_name) == sa.func.lower(target_name))
            .all()
        )
        if len(lines) > 1:
            logger.warning(
                'Returning the first of %s cell lines found for target_name %s' %
                (len(lines), target_name)
            )
        if not lines:
            logger.warning("No cells lines found for target name '%s'" % target_name)
            return None

        return cls(lines[0])


    def insert_resorted_line(self, session, sort_count, sort_date):
        '''
        Insert a polyclonal line produced by re-sorting the existing polyclonal line
        '''
        # do a crude check for uniqueness
        # (this is necessary because there is no unique constraint on
        # (parent_id, crispr_design_id, sort_count))
        for line in ([self.line] + self.line.children):
            if line.sort_count == sort_count:
                logger.warning(
                    'A resorted cell line with sort_count=%s already exists, '
                    'so no cell line will be created'
                    % sort_count
                )
                return

        resorted_line = models.CellLine(
            parent_id=self.line.id,
            crispr_design=self.line.crispr_design,
            line_type='POLYCLONAL',
            sort_date=sort_date,
            sort_count=sort_count
        )
        utils.add_and_commit(session, resorted_line)


    def insert_facs_dataset(self, session, histograms, scalars):
        '''
        Insert the processed FACS data for a single polyclonal cell line
        '''
        if self.line.facs_dataset:
            utils.delete_and_commit(session, self.line.facs_dataset)

        facs_dataset = models.FACSDataset(
            cell_line=self.line,
            scalars=utils.to_jsonable(scalars),
            histograms=utils.to_jsonable(histograms)
        )
        utils.add_and_commit(session, facs_dataset)


    def insert_sequencing_dataset(self, session, scalars):
        '''
        Insert processed amplicon sequencing results
        scalars: dict of percentages with keys ('hdr', 'nhej', 'other')
        '''
        if self.line.sequencing_dataset:
            utils.delete_and_commit(session, self.line.sequencing_dataset)

        sequencing_dataset = models.SequencingDataset(
            cell_line=self.line,
            scalars=utils.to_jsonable(scalars)
        )
        utils.add_and_commit(session, sequencing_dataset)


    def insert_microscopy_fovs(self, session, metadata):
        '''
        Insert a set of microscopy FOVs for the cell line

        metadata : dataframe of raw FOV metadata with the following columns:
        pml_id, imaging_round_id, site_num, raw_filepath
        '''
        fovs = [
            models.MicroscopyFOV(
                cell_line=self.line,
                pml_id=row.pml_id,
                site_num=row.site_num,
                raw_filename=row.raw_filepath,
                imaging_round_id=row.imaging_round_id,
            )
            for _, row in metadata.iterrows()
        ]
        utils.add_and_commit(session, fovs)
