import argparse
import logging
import os

from opencell.api import settings
from opencell.cli import utils as cli_utils
from opencell.database import metadata_operations, file_utils, constants

logger = logging.getLogger(__name__)


def populate(session, library_snapshot_filepath, electroporation_history_filepath):
    '''
    Initialize and populate the opencell database,
    using a set of 'snapshot' CSVs of various google spreadsheets

    This inserts the plate designs, crispr designs, and polyclonal lines
    for Plates 1-19.

    Note that this method has no ongoing use in production;
    it was used during development and to initialize the original opencell database,
    but is now used only to set up test databases.

    To insert crispr designs for new plates into an existing prod database,
    the `insert_plate_design` method should be used.
    '''

    # create the progenitor cell line used for Plates 1-19
    # (note the hard-coded progenitor cell line name)
    metadata_operations.get_or_create_progenitor_cell_line(
        session,
        name=constants.PARENTAL_LINE_NAME,
        notes='mNG1-10 in HEK293',
        create=True
    )

    # insert the plate designs and crispr designs
    library_snapshot = file_utils.load_library_snapshot(library_snapshot_filepath)
    plate_ids = sorted(set(library_snapshot.plate_id))
    for plate_id in plate_ids:
        metadata_operations.insert_plate_design(session, plate_id, library_snapshot_filepath)

    # insert the electroporations and polyclonal lines
    electroporation_history = file_utils.load_electroporation_history(
        electroporation_history_filepath
    )
    for _, row in electroporation_history.iterrows():
        metadata_operations.insert_electroporation(session, row.plate_id, row.date)


def main():
    parser = argparse.ArgumentParser(
        description='Initial opencell database population from google-sheet snapshots'
    )
    parser = cli_utils.add_common_cli_args(parser)
    cli_utils.configure_logging()

    args = parser.parse_args()
    config = settings.get_config(args.mode)
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)
    session = interface.make_session()

    # hard-coded paths to snapshots of google sheets
    data_dir = os.path.join(
        config.PROJECT_ROOT, 'opencell', 'tests', 'artifacts', 'data', 'metadata'
    )
    library_snapshot_filepath = os.path.join(data_dir, '2019-06-26_mNG11_HEK_library.csv')
    electroporation_history_filepath = os.path.join(data_dir, '2019-06-24_electroporations.csv')

    populate(session, library_snapshot_filepath, electroporation_history_filepath)


if __name__ == "__main__":
    main()
