import argparse
import logging
import pandas as pd
import numpy as np

from opencell.cli import utils as cli_utils
from opencell.cli import database as db_cli
from opencell.database import models, utils

logger = logging.getLogger(__name__)


def _impute_protein_concentration(measured_transcript_expression):
    '''
    The protein concentration imputed from transcript expression
    using linear regression in log-log space
    (intended as an estimate of abundance for proteins without a measured abundance)
    '''
    if pd.isna(measured_transcript_expression):
        return None

    # the number of copies per cell per nanomolar (from Marco)
    # (this is derived from the volume used to calculate protein concentration from copy number)
    copies_per_cell_per_nanomolar = 602

    # regression coefficients from Kibeom on 2021-09-15
    slope = 1.226
    offset = -0.06718
    imputed_protein_concentration = (
        10**(slope * np.log10(measured_transcript_expression) + offset)
    )
    if imputed_protein_concentration * copies_per_cell_per_nanomolar < 1:
        imputed_protein_concentration = None
    return imputed_protein_concentration


def _insert_abundance_measurements(interface, filepath):
    '''
    filepath : local path to a CSV file of RNA and protein abundance measurements in HEK293
        this should have columns 'uniprot_id', 'hek_rna_tpm' and 'hek_conc_nm'
    '''
    abundance = pd.read_csv(filepath)
    abundance.rename(columns={col: col.lower() for col in abundance.columns}, inplace=True)

    # drop any rows without a uniprot_id or RNA-seq data
    abundance.dropna(how='any', subset=['uniprot_id', 'hek_rna_tpm'], axis=0, inplace=True)

    # drop uniprot_ids that are not 'truly' expressed
    # the threshold value is from Manu on 2022-02-24
    minimum_true_expression_level = 1
    abundance = abundance.loc[abundance.hek_rna_tpm > minimum_true_expression_level]

    # eliminate any isoforms
    abundance['uniprot_id'] = abundance.uniprot_id.apply(lambda s: s.split('-')[0])

    # a few uniprot_ids are repeated, but the data is the same
    abundance = abundance.groupby('uniprot_id').first().reset_index()

    # drop uniprot_ids that are not found in the ensembl-uniprot assoc table
    extant_uniprot_ids = pd.read_sql(
        'select distinct(uniprot_id) from ensembl_uniprot_association', interface.engine
    )
    abundance = abundance.loc[abundance.uniprot_id.isin(extant_uniprot_ids.uniprot_id)]

    rows = []
    for _, row in abundance.iterrows():
        row = models.AbundanceMeasurement(
            uniprot_id=row.uniprot_id,
            gene_name=row.gene_name,
            measured_transcript_expression=row.hek_rna_tpm,
            measured_protein_concentration=row.hek_conc_nm,
            imputed_protein_concentration=_impute_protein_concentration(row.hek_rna_tpm),
        )
        rows.append(row)

    session = interface.make_session()
    utils.add_and_commit(session, rows)


def main():
    cli_utils.configure_logging()
    parser = argparse.ArgumentParser(description='Insert protein abundance measurements')
    parser = cli_utils.add_common_cli_args(parser)

    # the path to the CSV of abundance measurements
    parser.add_argument('--filepath', dest='filepath')

    args = parser.parse_args()
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)

    # clear the existing table
    db_cli._execute_sql('truncate abundance_measurement;', interface)

    _insert_abundance_measurements(interface, args.filepath)


if __name__ == "__main__":
    main()
