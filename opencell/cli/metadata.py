import argparse
import dask
import dask.diagnostics
import logging
import pandas as pd

from opencell.cli import utils as cli_utils
from opencell.database import (
    models, metadata_operations, reference_datasets, uniprot_operations
)

logger = logging.getLogger(__name__)


def parse_args():
    '''
    '''
    parser = argparse.ArgumentParser()
    parser = cli_utils.add_common_cli_args(parser)
    cli_utils.configure_logging()

    # the filepath to a snapshot of a google sheet, for methods that need one
    # (e.g. the 'da list' sheet, the pipeline-microscopy-master-key, or the resorted lines sheet)
    parser.add_argument('--snapshot-filepath', dest='snapshot_filepath')

    # plate_id is used by insert_plate_design and insert_electroporation
    parser.add_argument('--plate-id', dest='plate_id')

    # date is used by insert_electroporation
    parser.add_argument('--date', dest='date')

    # CLI args whose presence in the command sets them to True
    action_arg_dests = [
        'update_existing',
        'insert_plate_design',
        'insert_electroporation',
        'insert_resorted_lines',
        'insert_uniprot_metadata_for_crispr_designs',
        'insert_uniprot_metadata_for_protein_groups',
        'insert_hgnc_metadata',
        'insert_ensembl_uniprot_association',
        'insert_uniprotkb_metadata',
    ]

    for dest in action_arg_dests:
        flag = '--%s' % dest.replace('_', '-')
        parser.add_argument(flag, dest=dest, action='store_true', required=False)
        parser.set_defaults(**{dest: False})

    args = parser.parse_args()
    return args


def insert_uniprot_metadata_for_crispr_designs(Session):
    '''
    Retrieve and insert uniprot metadata for all crispr designs
    '''
    @dask.delayed
    def create_task(Session, design_id):
        uniprot_operations.insert_uniprot_metadata_for_crispr_design(Session(), design_id)

    designs = Session.query(models.CrisprDesign).all()
    tasks = [create_task(Session, design.id) for design in designs]

    with dask.diagnostics.ProgressBar():
        dask.compute(*tasks)


def insert_uniprot_metadata_for_protein_groups(Session):
    '''
    Insert uniprot metadata for all uniprot_ids that appear in at least one
    mass spec protein group and for which metadata does not already exist
    '''
    engine = Session.get_bind()

    # all uniprot_ids from all mass spec protein groups
    all_uniprot_ids = (
        pd.read_sql(
            'select unnest(uniprot_ids) as uniprot_id from mass_spec_protein_group',
            engine
        )
        .uniprot_id
        .tolist()
    )

    # unique ids, ignoring isoforms (which are indicated by trailing dashed numbers)
    all_uniprot_ids = set([uniprot_id.split('-')[0] for uniprot_id in all_uniprot_ids])

    new_uniprot_ids = all_uniprot_ids.difference([
        row.uniprot_id for row in Session.query(models.UniprotMetadata).all()
    ])

    @dask.delayed
    def create_task(Session, uniprot_id):
        uniprot_operations.insert_uniprot_metadata_from_id(Session(), uniprot_id)

    tasks = [create_task(Session, uniprot_id) for uniprot_id in new_uniprot_ids]
    with dask.diagnostics.ProgressBar():
        dask.compute(*tasks)


def main():
    # TODO: add optional file handler to the logger

    args = parse_args()
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)

    # note: a scoped session is required for dask-delayed uniprot-metadata-retrieval methods
    Session = interface.make_scoped_session()

    if args.insert_plate_design:
        metadata_operations.insert_plate_design(Session, args.plate_id, args.snapshot_filepath)

    if args.insert_electroporation:
        metadata_operations.insert_electroporation(
            Session, plate_id=args.plate_id, electroporation_date=args.date
        )

    if args.insert_resorted_lines:
        platemap = pd.read_csv(args.snapshot_filepath)
        metadata_operations.insert_resorted_lines(Session, platemap)

    if args.insert_uniprot_metadata_for_crispr_designs:
        insert_uniprot_metadata_for_crispr_designs(Session)

    if args.insert_uniprot_metadata_for_protein_groups:
        insert_uniprot_metadata_for_protein_groups(Session)

    if args.insert_hgnc_metadata:
        reference_datasets.populate_hgnc_metadata(Session)

    if args.insert_ensembl_uniprot_association:
        reference_datasets.populate_ensembl_uniprot_association(Session)

    if args.insert_uniprotkb_metadata:
        reference_datasets.populate_uniprotkb_metadata(Session, dirpath=args.snapshot_filepath)


if __name__ == '__main__':
    main()
