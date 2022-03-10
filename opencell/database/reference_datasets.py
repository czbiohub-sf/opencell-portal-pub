import dask
import dask.diagnostics
import json
import logging
import pandas as pd
import pathlib
import numpy as np
import re

from opencell.database import models, utils

logger = logging.getLogger(__name__)
REFERENCE_DATASETS_DIR = pathlib.Path(__file__).parent.parent.parent / 'reference-datasets'


def compare_sets(column=None, ref=None, **kwargs):
    '''
    Convenience method to compare sets of ids
    '''
    vals = kwargs.copy()
    if column is not None:
        ref = ref[column]
        for key, val in kwargs.items():
            vals[key] = set(val[column])

    ref = set(ref)
    print('Number unique in:')
    print('%-20s %s' % ('ref', len(ref)))
    for key, val in vals.items():
        print('%-20s %s' % (key, len(set(val))))

    print('\nNumber in ref but not in:')
    for key, val in vals.items():
        print('%-20s %s' % (key, len(ref.difference(val))))

    print('\nNumber not in ref but in:')
    for key, val in vals.items():
        print('%-20s %s' % (key, len(set(val).difference(ref))))


def load_all_ensg_ids(primary_only=False):
    '''
    Load an export of ensg_ids and their chromosome names for all human genes

    This dataset was exported manually from Biomart on 2021-09-17 by selecting the dataset
    'Human genes (GRCh38.p13)' with no filters and these attributes:
        - 'Gene stable ID'
        - 'Chromosome/scaffold name'

    primary_only : whether to drop ensg_ids that correspond to 'non-primary' sequences
        (either alternative sequences from haplotypic regions or unlocalized contigs)
    '''
    ens_all = pd.read_csv(
        REFERENCE_DATASETS_DIR / '2021-09-17-biomart-export-GRCh38.p13.txt'
    )
    ens_all.rename(
        columns={col: col.replace(' ', '_').replace('/', '_').lower() for col in ens_all.columns},
        inplace=True
    )
    ens_all.rename(
        columns={'gene_stable_id': 'ensg_id', 'uniprotkb_swiss-prot_id': 'uniprot_id'},
        inplace=True
    )

    if primary_only:
        # drop rows with contig names that do not correspond to chromosomes
        chromosome_names = list(map(str, range(1, 23))) + ['X', 'Y', 'MT']
        ens_all = ens_all.loc[ens_all.chromosome_scaffold_name.isin(chromosome_names)]

    # drop unneeded columns
    ens_all = ens_all[[
        'ensg_id', 'uniprot_id', 'chromosome_scaffold_name', 'gene_name', 'gene_description'
    ]]
    return ens_all


def load_ensembl_uniprot_map(primary_only=False):
    '''
    This is an export of ENSG/T/P ids and their corresponding uniprot ids
    It was downloaded manually on 2021-09-16 from:
    http://ftp.ensembl.org/pub/release-104/tsv/homo_sapiens/Homo_sapiens.GRCh38.104.uniprot.tsv.gz

    Note that it includes non-primary ensg_ids
    (that is, for alternative sequences from haplotypic regions)
    but does not include the contig names necessary to identify them
    '''
    ens_unp_map = pd.read_csv(
        REFERENCE_DATASETS_DIR / '2021-09-16-Homo_sapiens.GRCh38.104.uniprot.tsv',
        sep='\t'
    )
    ens_unp_map = ens_unp_map.rename(columns={'gene_stable_id': 'ensg_id', 'xref': 'uniprot_id'})

    # drop the entries without either an ensg_id or unniprot_id
    # (there's nothing we can do with these)
    ens_unp_map = ens_unp_map.dropna(axis=0, subset=['ensg_id', 'uniprot_id'], how='all')

    # drop isoforms from the uniprot_ids
    ens_unp_map['uniprot_id'] = ens_unp_map.uniprot_id.apply(lambda d: d.split('-')[0])

    # drop duplicates
    ens_unp_map = ens_unp_map.groupby(['ensg_id', 'uniprot_id']).first().reset_index()

    # drop unneeded columns
    ens_unp_map = ens_unp_map[['ensg_id', 'uniprot_id', 'db_name', 'info_type']]

    if primary_only:
        ens_primary = load_all_ensg_ids(primary_only=True)
        ens_unp_map = ens_unp_map.loc[ens_unp_map.ensg_id.isin(ens_primary.ensg_id)]

    return ens_unp_map


def load_hgnc_dataset(clean=False, primary_only=False, dedup=False):
    '''
    This is the HGNC dataset for protein-coding genes

    It was downloaded manually on 2021-09-18 from:
    http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/locus_groups/protein-coding_gene.txt

    clean : drops extraneous columns, rows without ensg_ids or uniprot_ids,
        and duplicated (ensg_id, uniprot_id) pairs
    primary_only : drops non-primary ensg_ids
    dedup : eliminates duplicated hgnc_ids by dropping the uniprot_id column
        (because there are multiple uniprot_ids for some hgnc_ids)
    '''

    hgnc = pd.read_csv(
        REFERENCE_DATASETS_DIR / '2021-09-18-HGNC-protein-coding_gene.txt',
        low_memory=False,
        sep='\t'
    )
    hgnc.rename(columns={'ensembl_gene_id': 'ensg_id'}, inplace=True)

    hgnc['uniprot_id'] = hgnc.uniprot_ids.str.split('|')
    hgnc = hgnc.explode('uniprot_id')

    if clean:
        # drop the entries without either an ensg_id or unniprot_id
        # (there's nothing we can do with these)
        hgnc = hgnc.dropna(axis=0, subset=['ensg_id', 'uniprot_id'], how='all')

        # drop the NAs and any duplicates
        hgnc = hgnc.groupby(['ensg_id', 'uniprot_id']).first().reset_index()

        # drop most columns
        hgnc = hgnc[[
            'hgnc_id', 'ensg_id', 'uniprot_id',
            'symbol', 'alias_symbol', 'prev_symbol',
            'name', 'alias_name', 'prev_name',
        ]]
        # check for 1-to-1 correspondence between hgnc_id and ensg_id
        # (this assumption is important but implicit in downstream methods)
        assert hgnc.hgnc_id.unique().shape == hgnc.ensg_id.unique().shape

    if primary_only:
        ens_primary = load_all_ensg_ids(primary_only=True)
        hgnc = hgnc.loc[hgnc.ensg_id.isin(ens_primary.ensg_id)]

    if dedup:
        hgnc = hgnc.groupby('hgnc_id').first().reset_index().drop(labels=['uniprot_id'], axis=1)

    return hgnc


def generate_primary_ensg_to_uniprot_map():
    '''
    This generates the final consensus map between primary ensg_ids and uniprot_ids

    It does two things:
    1) drops ensg_ids that are not in both the ensembl-uniprot map from ensembl
        and the HGNC protein-coding genes dataset
    2) combines the ensg_id - uniprot_id maps from ensembl and HGNC
        (in order to include a few (ensg_id, uniprot_id) pairs that are found in HGNC
        but not in the ensembl map)
    '''
    ens_unp_map = load_ensembl_uniprot_map(primary_only=True)
    hgnc = load_hgnc_dataset(clean=True, primary_only=True, dedup=False)

    # merge hgnc into ens_unp_map on ensg_id (this drops ensg_ids not in both datasets)
    ens_unp_map = pd.merge(
        hgnc[['ensg_id', 'uniprot_id']],
        ens_unp_map[['ensg_id', 'uniprot_id']],
        left_on='ensg_id',
        right_on='ensg_id',
        how='inner'
    )

    # aggregate the uniprot_ids in the two uniprot_id columns into lists
    # (one column is from HGNC and the other is from ens_unp_map)
    ens_unp_map = (
        ens_unp_map.groupby('ensg_id')
        .agg({'uniprot_id_x': set, 'uniprot_id_y': set})
        .reset_index()
    )

    # concatenate the lists of uniprot_ids
    ens_unp_map['uniprot_id'] = None
    for ind, row in ens_unp_map.iterrows():
        ens_unp_map.at[ind, 'uniprot_id'] = list(row.uniprot_id_x.union(row.uniprot_id_y))

    # this is the final map from ensg_id to uniprot_id
    ens_unp_map = ens_unp_map[['ensg_id', 'uniprot_id']].explode('uniprot_id')

    return ens_unp_map


class UniProtKBEntryParser:
    '''
    Methods to parse an entry in a UniProtKB proteome dataset
    in order to populate the uniprotkb_metadata table
    The schema of this export is documented here: https://web.expasy.org/docs/userman.html

    For reference, here is a representative subset of the lines for the POLR2F entry:
    ```
    ID   RPAB2_HUMAN             Reviewed;         127 AA.
    AC   P61218; P41584; Q6IAY3;
    DT   10-MAY-2004, integrated into UniProtKB/Swiss-Prot.
    DT   10-MAY-2004, sequence version 1.
    DT   29-SEP-2021, entry version 167.
    DE   RecName: Full=DNA-directed RNA polymerases I, II, and III subunit RPABC2;
    DE            Short=RNA polymerases I, II, and III subunit ABC2;
    GN   Name=POLR2F; Synonyms=POLRF;
    OS   Homo sapiens (Human).
    OC   Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia;
    OC   Eutheria; Euarchontoglires; Primates; Haplorrhini; Catarrhini; Hominidae;
    OC   Homo.
    OX   NCBI_TaxID=9606;
    CC   -!- FUNCTION: DNA-dependent RNA polymerases catalyze the transcription of
    CC       DNA into RNA using the four ribonucleoside triphosphates as substrates.
    ```
    '''
    def __init__(self, lines):
        '''
        lines : a list of raw lines corresponding to a single UniProtKB entry
        '''
        self.lines = tuple(lines)

        # all parsed data, updated in-place by parsing methods
        self.parsed_data = {}

    def parse_for_db(self):
        '''
        Convenience method to parse the data needed to populate the uniprotkb_metadata table
        '''
        self.parse_uniprot_ids()
        self.parse_entry_name()
        self.parse_gene_name()
        self.parse_comment(topic='function')

    def parse_entry_name(self):
        '''
        Parse the entry name and entry status from the first line
        (the entry names are specific to UniProtKB and are of the form 'ATLA3_HUMAN')

        Note: the regex fails for isoforms, whose entry_names contain dashes (e.g. 'ARAP1-2_HUMAN'),
        but this is okay because we do not need to ingest isoform entries
        '''
        self.parsed_data.update({'entry_name': '', 'status': '', 'length': ''})

        result = re.findall(r'^ID   (\w+) +(\w+); +([0-9]+) AA', self.lines[0])
        if not result:
            return
        entry_name, status, length = result[0]
        self.parsed_data.update({'entry_name': entry_name, 'status': status, 'length': length})

    def parse_uniprot_ids(self):
        '''
        Parse the list of uniprot_ids from all of the 'AC' lines
        (note that the UniProt docs refer to 'uniprot_ids' as 'accession numbers')
        '''
        prefix = 'AC   '
        uniprot_ids = []
        for line in self.lines:
            if line.startswith(prefix):
                uniprot_ids.extend(line.replace(prefix, '').strip().split(';'))

        uniprot_ids = [uniprot_id.strip() for uniprot_id in uniprot_ids if uniprot_id]

        # by convention, the first id in the list is the 'primary' id,
        # and the remaining ids (which are in alphabetical order) are 'secondary' ids
        self.parsed_data.update(
            {'primary_uniprot_id': uniprot_ids[0], 'secondary_uniprot_ids': uniprot_ids[1:]}
        )

    def parse_gene_name(self):
        '''
        Parse the first gene name from the first 'GN' line, if any
        '''
        prefix = 'GN   '
        gene_names = []
        for line in self.lines:
            if line.startswith(prefix):
                gene_names = re.findall(r'^GN   Name=(\w+).+', line)
                break
        self.parsed_data.update({'gene_name': gene_names[0] if gene_names else ''})

    def parse_comment(self, topic):
        '''
        Parse the *first* comment for the given topic from the entry
        (note that entries may have more than one comment for a given topic)
        topic : a valid comment topic; examples include 'FUNCTION', 'SUBUNIT', 'INTERACTION'

        For reference, here is a mock comment block,
        including the copyright notice that appears at the end the block:
        ```
        CC   -!- FUNCTION: First function comment. This may take up one line
        CC       or multiple lines.
        CC   -!- FUNCTION: A second function comment.
        CC   -!- SUBUNIT: Beginning of the 'subunit' comment.
        CC       This would be the second line of the subunit comment.
        CC   ---------------------------------------------------------------------------
        CC   Copyrighted by the UniProt Consortium, see https://www.uniprot.org/terms
        ```
        Note that the comment(s) under the 'FUNCTION' topic correspond to what we call
        the 'functional annotations' from UniProt.
        '''

        key = f"{topic.lower().replace(' ', '_')}_comment"
        self.parsed_data[key] = ''

        # the beginning of all lines in the comment block
        prefix = 'CC   '

        # the beginning of the first line of a new topic block within the comment block
        generic_topic_prefix = f'{prefix}-!- '

        # the beginning of the first line of a new topic block for the given topic
        # (for example: 'CC   -!- FUNCTION: ')
        this_topic_prefix = f'{generic_topic_prefix}{topic.upper()}: '

        # find the first line of the first comment block for the topic
        comment_lines = []
        for ind, line in enumerate(self.lines):
            if line.startswith(this_topic_prefix):
                comment_lines = [line.replace(this_topic_prefix, '')]
                break

        if not comment_lines:
            return

        # append lines until we reach the next comment block or the end of all comment blocks
        for line in self.lines[(ind + 1):]:
            if (
                # the line is the start of another comment-topic block (of any topic)
                line.startswith(generic_topic_prefix)

                # the line is the first line of the copyright warning after all comment blocks
                or line.startswith(f'{prefix}----')

                # there is no copyright warning and the line is the start of another block type
                # (unclear if this ever happens)
                or not line.startswith(prefix)
            ):
                break

            # drop the CC prefix
            line = re.sub(r'^CC [ ]+', '', line)

            comment_lines.append(line)

        comment = ''.join(comment_lines).replace('\n', ' ').strip()
        self.parsed_data[key] = comment


def load_uniprotkb_entries(filepath):
    '''
    Load a raw UniProtKB dataset and break it up into lines corresponding to each entry

    Intended for use with the human UniProtKB dataset:
    https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/Eukaryota/UP000005640/

    The schema of these files is documented here: https://web.expasy.org/docs/userman.html
    '''
    with open(filepath) as file:
        lines = file.readlines()

    # retain only lines containing the entry name, uniprot_ids, gene names, and comments
    relevant_line_codes = ('ID', 'AC', 'GN', 'CC')
    lines = [line for line in lines if line[:2] in relevant_line_codes]

    # break up the lines into entries,
    # using the fact that each entry begins with a single 'ID' line code
    entry_inds = [ind for ind, line in enumerate(lines) if line.startswith('ID')]
    entries = [lines[entry_inds[ind - 1]:entry_inds[ind]] for ind in range(1, len(entry_inds))]

    # append the very last entry
    entries.append(lines[entry_inds[-1]:])
    return entries


def parse_uniprotkb_entries(entries):
    '''
    Parse all raw uniprot entries and return a dataframe suitable for bulk-insertion
    into the uniprotkb_metadata table
    '''
    def task(entry):
        parser = UniProtKBEntryParser(entry)
        parser.parse_for_db()
        return parser.parsed_data

    with dask.diagnostics.ProgressBar():
        rows = dask.compute(*[task(entry) for entry in entries])

    df = pd.DataFrame(data=rows)
    return df


def populate_hgnc_metadata(session):
    '''
    This inserts the cleaned, primary-ensg-only, de-duped HGNC dataset
    into the hgnc_metadata table
    '''
    engine = session.get_bind()
    table_name = 'hgnc_metadata'

    logger.info('Truncating the %s table' % table_name)
    engine.execute('truncate %s cascade;' % table_name)

    # coerce np.nan to None
    hgnc = load_hgnc_dataset(clean=True, primary_only=True, dedup=True)
    rows = json.loads(hgnc.to_json(orient='records'))

    logger.info('Populating %s table with %s rows' % (table_name, len(rows)))
    session.bulk_insert_mappings(models.HGNCMetadata, rows)
    session.commit()


def populate_ensembl_uniprot_association(session):
    '''
    This inserts the final reference map between (primary) ensg_ids and uniprot_ids
    '''
    engine = session.get_bind()
    table_name = 'ensembl_uniprot_association'

    logger.info('Truncating the %s table' % table_name)
    engine.execute('truncate %s;' % table_name)

    df = generate_primary_ensg_to_uniprot_map()
    rows = json.loads(df.to_json(orient='records'))

    logger.info('Populating the %s table with %s rows ' % (table_name, len(rows)))
    session.bulk_insert_mappings(models.EnsemblUniprotAssociation, rows)
    session.commit()


def populate_uniprotkb_metadata(session, dirpath):
    '''
    Insert metadata parsed from the UniprotKB entries
    dirpath : local directory containing the files
        'UP000005640_9606.dat'
        'UP000005640_9606_additional.dat'

    These files are retrieved from the UniProtKB FTP server here:
    https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/Eukaryota/UP000005640/
    '''
    dirpath = pathlib.Path(dirpath)

    engine = session.get_bind()
    table_name = 'uniprotkb_metadata'

    logger.info('Truncating the %s table' % table_name)
    engine.execute('truncate %s;' % table_name)

    # parse all entries from the primary .dat file
    entries = load_uniprotkb_entries(dirpath / 'UP000005640_9606.dat')
    df = parse_uniprotkb_entries(entries)

    # parse all entries from the additional .dat file
    entries = load_uniprotkb_entries(dirpath / 'UP000005640_9606_additional.dat')
    df_additional = parse_uniprotkb_entries(entries)

    # there are 74 reviewed entries in the additional file, and we need to include them
    # (unclear why they are not in the primary file)
    df_additional_reviewed = df_additional.loc[df_additional.status == 'Reviewed']
    df = pd.concat((df, df_additional_reviewed), axis=0)

    rows = json.loads(df.to_json(orient='records'))
    logger.info('Populating the %s table with %s rows ' % (table_name, len(rows)))
    session.bulk_insert_mappings(models.UniprotKBMetadata, rows)
    session.commit()
