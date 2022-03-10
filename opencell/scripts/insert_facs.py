import argparse
import json
import logging
import pandas as pd
import os

from opencell.cli import utils as cli_utils
from opencell.database import metadata_operations, utils

logger = logging.getLogger(__name__)


def insert_facs(session, facs_results_dir):
    '''
    Insert FACS results and histograms for the original polyclonal cell lines from Plates 1-19
    '''
    # hard-coded filenames of the cached FACS results
    results_filepath = os.path.join(facs_results_dir, 'facs-results.csv')
    histograms_filepath = os.path.join(facs_results_dir, 'facs-histograms.json')

    facs_properties = pd.read_csv(results_filepath)
    with open(histograms_filepath, 'r') as file:
        facs_histograms = json.load(file)

    # key the histograms by tuples of (plate_id, well_id)
    d = {}
    for row in facs_histograms:
        d[(row['plate_id'], row['well_id'])] = row
    facs_histograms = d

    for _, row in facs_properties.iterrows():
        line_ops = metadata_operations.PolyclonalLineOperations.from_plate_well(
            session, row.plate_id, utils.format_well_id(row.well_id), sort_count=1
        )
        if not line_ops:
            continue

        # the histograms are dicts of 'x', 'y_sample', 'y_fitted_ref'
        # (note row.well_id is an unformatted well_id)
        histograms = facs_histograms.get((row.plate_id, row.well_id))
        scalars = dict(row.drop(['plate_id', 'well_id']))
        line_ops.insert_facs_dataset(session, histograms=histograms, scalars=scalars)


def main():
    cli_utils.configure_logging()
    parser = argparse.ArgumentParser(description='Insert processed FACS results')
    parser = cli_utils.add_common_cli_args(parser)

    # the path to the directory of cached FACS results
    parser.add_argument('--facs-results-dir', dest='facs_results_dir')

    args = parser.parse_args()
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)
    session = interface.make_session()

    insert_facs(session, args.facs_results_dir)


if __name__ == "__main__":
    main()
