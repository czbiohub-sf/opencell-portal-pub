# flake8: noqa
import argparse
import io
import logging
import os
import pandas as pd
import pathlib
import requests
from sqlalchemy import column

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# the URL to the updated opencell preprint
BIORXIV_URL = 'https://www.biorxiv.org/content/biorxiv/early/2021/12/08/2021.03.29.437450/'

# manually-curated URLs, sheet names, and column definitions for the supp tables
# that also need to appear on the data-download page of the opencell website
# note that the column defs were manually copied from the 'readme' sheets of the supp tables
# fmt: off
TABLE_METADATA = {
    'library-metadata': {
        'biorxiv_endpoint': 'DC2/embed/media-2.xlsx',
        'sheet_name': 'OC_library',
        'column_defs': (
            '''
            gene_name,canonical gene name for the OpenCell target
            Uniprot_ID,corresponding Uniprot protein ID
            Protein_name,corresponding Uniprot protein name
            Ensembl_gene_ID,corresponding Ensembl gene ID
            Ensembl_transcript_ID,Ensembl transcript ID used for design
            tagged_terminus,site for mNG11 tag insertion
            insertion_justification_type,type of information for how the insertion site was chosen
            insertion_justification_reference,specific information supporting the choice of insertion site
            insertion_justification_notes,notes relating to insertion site
            protospacer_sequence,nucleotide sequence of the Cas9 gRNA protospacer used for genomic cleavage
            HDR_donor_sequence,nucleotide sequence of homology ssODN donor provided for templating homology directed repair
            fwd_genomic_primer,nucleotide sequence of the forward primer used for genotyping PCR
            rev_genomic_primer,nucleotide sequence of the reverse primer used for genotyping PCR
            fraction_wt_alleles,genotype analysis of the selected polyclonal pool for the corresponding OpenCell target: fraction of unedited alleles (wild-type) for the OpenCell target
            fraction_mNG11_integrated_alleles,genotype analysis of the selected polyclonal pool for the corresponding OpenCell target: fraction of mNG11-integrated alleles (the desired insertion product) for the OpenCell target
            fraction_other_alleles,genotype analysis of the selected polyclonal pool for the corresponding OpenCell target: fraction of alleles harboring non-functional mutations for the OpenCell target
            '''
        ),
        'column_renaming': {
            'Ensembl_gene_ID': 'ensg_id',
            'Ensembl_transcript_ID': 'enst_id',
        },
        'sort_by': 'gene_name',
    },
    'protein-abundance': {
        'biorxiv_endpoint': 'DC3/embed/media-3.xlsx',
        'sheet_name': 'Suppl_Table_2_annotated_HEK293T',
        'column_defs': (
            '''
            gene_name,canonical gene name
            ENSG,corresponding Ensembl gene ID
            major_coding_ENST,corresponding Ensembl transcript ID
            Uniprot_ID,corresponding Uniprot protein ID
            protein_name,canonical protein name
            hek_RNA_tpm,transcript expression level from RNASeq analysis in transcript per million (tpm)
            hek_conc_nM,intracellular protein concentration measured by mass spectrometry (in nmole/L)
            hek_protein_copy_number,protein copy number per cell measured by mass spectrometry
            '''
        ),
        'column_renaming': {
            'ENSG': 'ensg_id',
            'major_coding_ENST': 'enst_id',
            'hek_conc_nM': 'hek_protein_conc_nM',
        },
        # adds the hek_protein_copy_number column
        'callable': 'append_copy_number',
        'sort_by': 'gene_name',
    },
    'protein-interactions': {
        'biorxiv_endpoint': 'DC5/embed/media-5.xlsx',
        'sheet_name': 'all_interactions',
        'column_defs': (
            '''
            target_gene_name,canonical gene name for the OpenCell target (pull-down bait)
            interactor_gene_name,canonical gene name for the interactor (pull-down prey)
            target_ensg_id,Ensembl gene ID for the OpenCell target
            interactor_ensg_id,Ensembl gene ID for the OpenCell prey
            interactor_protein_ids,Uniprot gene IDs for all interactor proteins/isoforms identified in the mass-spectrometry
            pvals,p-value for enrichment (Student's t-test for triplicate set)
            enrichment,enrichment of a specific interactor in the target's pull-down
            interaction_stoi,stoichiometry of abundance between bait and prey in a given pull-down
            abundance_stoi,stoichiometry of abundance between bait and prey in the whole cell
            '''
        ),
        'column_renaming': {
            'target_ensg': 'target_ensg_id',
            'interactor_ensg': 'interactor_ensg_id',
            'interactor_protein_ids': 'interactor_uniprot_ids',
            'pvals': 'pval',
            'interaction_stoi': 'interaction_stoichiometry',
            'abundance_stoi': 'abundance_stoichiometry',
        },
        'sort_by': ['target_gene_name', 'interactor_gene_name'],
    },
    'localization-annotations': {
        'biorxiv_endpoint': 'DC7/embed/media-7.xlsx',
        'sheet_name': 'localization_annotations',
        'column_defs': (
            '''
            target_name,canonical gene name for the OpenCell target
            ensg_id,Ensembl gene ID for the OpenCell target
            annotations_grade_3,all grade 3 annotations for the OpenCell target
            annotations_grade_2,all grade 2 annotations for the OpenCell target
            annotations_grade_1,all grade 1 annotations for the OpenCell target
            '''
        ),
        'sort_by': 'target_name',
    },
}
# fmt: on


def append_copy_number(df):
    '''
    Append protein copy number column to the protein-abundance sheet
    '''
    # the number of copies per cell per nanomolar (from Marco)
    copies_per_cell_per_nanomolar = 602
    df['hek_protein_copy_number'] = df.hek_protein_conc_nm * copies_per_cell_per_nanomolar
    return df


def cleanup_column_name(name):
    return name.strip().lower().replace('-', '_').replace(' ', '_')


def _process_table(output_dirpath, table_name, table_metadata):
    '''
    '''
    sheet_filepath = output_dirpath / f'opencell-{table_name}.csv'
    column_defs_filepath = output_dirpath / f'opencell-{table_name}-readme.csv'

    if os.path.isfile(sheet_filepath):
        logger.info("Skipping table '%s' because a CSV file already exists" % table_name)
        return

    # retrieve the raw excel spreadsheets from biorxiv
    response = requests.get(f"{BIORXIV_URL}{table_metadata['biorxiv_endpoint']}")
    with io.BytesIO(initial_bytes=response.content) as file:
        sheet = pd.read_excel(file, sheet_name=table_metadata['sheet_name'])

    # load the hard-coded column definitions
    with io.StringIO(initial_value=table_metadata['column_defs'].strip()) as file:
        column_defs = pd.read_csv(file, sep=',', header=None)
        column_defs = column_defs.applymap(lambda s: s.strip())
        column_defs.columns = ['column_name', 'column_description']

    # hard-coded column renaming
    column_renaming = table_metadata.get('column_renaming')
    if column_renaming is not None:
        sheet.rename(columns=column_renaming, inplace=True)
        column_defs.replace(to_replace=column_renaming, value=None, inplace=True)

    # clean up column names
    sheet.rename(
        columns={column: cleanup_column_name(column) for column in sheet.columns},
        inplace=True
    )
    column_defs['column_name'] = column_defs.column_name.apply(cleanup_column_name)

    # call the callable to modify the dataframe, if any
    if table_metadata.get('callable'):
        sheet = globals()[table_metadata.get('callable')](sheet)

    if table_metadata.get('sort_by'):
        sheet = sheet.sort_values(by=table_metadata.get('sort_by'))

    # drop columns not in the hard-coded column definitions
    sheet = sheet[column_defs.column_name.tolist()]

    # save the sheet and the column defs
    sheet.to_csv(sheet_filepath, index=False)
    logger.info('Sheet exported as CSV to %s' % sheet_filepath)

    column_defs.to_csv(column_defs_filepath, index=False)
    logger.info('Column defs exported as CSV to %s' % column_defs_filepath)

    with pd.ExcelWriter(str(sheet_filepath).replace('.csv', '.xlsx')) as excel_file:
        sheet.to_excel(excel_file, sheet_name=table_name, index=False)
        column_defs.to_excel(excel_file, sheet_name='readme', index=False)


def main():
    '''
    This script retrieves and reformats certain of the supp tables
    from the 2021 OpenCell preprint in order to generate CSV files
    suitable for the download links on the 'Download data' page of the opencell frontend
    '''

    parser = argparse.ArgumentParser(description='Insert protein abundance measurements')

    # the path to the CSV of abundance measurements
    parser.add_argument('--generate', action='store_true', required=False)
    parser.add_argument('--upload', action='store_true', required=False)
    args = parser.parse_args()

    output_dirpath = pathlib.Path(__file__).parent.parent.parent / 'tmp' / 'datasets'
    os.makedirs(output_dirpath, exist_ok=True)

    if args.generate:
        for table_name, table_metadata in TABLE_METADATA.items():
            logger.info('Processing table %s' % table_name)
            _process_table(output_dirpath, table_name, table_metadata)

    # TODO: upload to s3://opencell
    if args.upload:
        pass


if __name__ == "__main__":
    main()
