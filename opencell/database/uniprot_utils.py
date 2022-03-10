import io
import logging
import pandas as pd
import re
import requests

logger = logging.getLogger(__name__)


def prettify_hgnc_protein_name(name):
    '''
    '''
    # capitalize the first letter
    name = name[0].upper() + name[1:]
    name = name.replace(' like', '-like')
    name = name.replace(' related', '-related')
    return name


def prettify_uniprot_protein_name(protein_names):
    '''
    Clean up a raw Uniprot protein name
    (this is a string in the uniprot_metadata.protein_names column)

    These names are messy: the 'primary' name that we want to retain appears first,
    followed by one or more synonymous names in parentheses,
    followed sometimes by a comment-like string wrapped in brackets.

    Examples
    --------
    ATL2
    'Atlastin-2 (EC 3.6.5.-) (ADP-ribosylation factor-like protein 6-interacting protein 2)'

    HNRNPH1
    'Heterogeneous nuclear ribonucleoprotein H (hnRNP H)
    [Cleaved into: Heterogeneous nuclear ribonucleoprotein H, N-terminally processed]'

    BUD23
    'Probable 18S rRNA (guanine-N(7))-methyltransferase (EC 2.1.1.-)'
    '''

    # note that this regex fails for the rare edge case in which parentheses appear
    # in the primary name itself (for example, BUD23)
    result = re.match(r'^(.*?)(?: \(.*?\))*(?: \[.*?\])?$', protein_names)
    if not result:
        return None
    return result.groups()[0]


def prettify_uniprot_annotation(annotation):
    '''
    Clean up a raw Uniprot functional annotation

    Examples
    --------
    'FUNCTION: GTPase tethering membranes through formation of trans-homooligomers
    and mediating homotypic fusion of endoplasmic reticulum membranes.
    Functions in endoplasmic reticulum tubular network biogenesis
    (PubMed:18270207, PubMed:19665976, PubMed:27619977).
    {ECO:0000269|PubMed:18270207, ECO:0000269|PubMed:19665976, ECO:0000269|PubMed:27619977}.'
    '''

    if pd.isna(annotation):
        return None

    # sometimes there are two annotations concatenated
    annotation = annotation.replace('; FUNCTION: ', ' ')
    annotation = annotation.replace('FUNCTION: ', '')

    # remove all paranthetical pubmed citations
    annotation = re.sub(r' \(((PubMed:[0-9]+)(, )?)+\)', '', annotation)

    # remove the trailing pubmed citations (always in brackets at the end)
    annotation = re.sub(r' {.*}.', '', annotation)
    return annotation


def query_uniprotkb(query, only_reviewed=True, limit=1):
    '''
    Search (the human) UniprotKB and return some useful metadata

    Parameters
    ----------
    query : one of many identifiers, including a protein name, a gene name,
        a uniprot_id, or an ENST ID.
    only_reviewed : whether to query only reviewed uniprot entries
    limit : how many results (sorted by 'relevance') to return

    Returns
    -------
    A dataframe of metadata (for column descriptions, see below)

    Asides
    ------
    These are additional query columns containing various specific gene name synonyms;
    as far as I can tell, these all also appear in the 'genes' column:
    'genes(PREFERRED)'
    'genes(ALTERNATIVE)'
    'genes(OLN)'
    'genes(ORF)'

    Also, it's not clear how to include the ENSG ID in the query results;
    there is a column for Ensembl IDs called 'database(Ensembl)'
    that returns both ENST and ENSG IDs via the web UI,
    but that only returns the ENST ID via the API call used here.
    '''

    url = 'https://www.uniprot.org/uniprot'

    # Define the UniprotKB columns to include in the search result.
    # These were selected by hand in the 'customize columns' page,
    # then the query names were extracted from the 'Share your results' URL,
    # and finally the query names were matched with the output names.
    # (Note that the output names are used to rename columns in the dataframe of search results
    # when a final_name is specified, otherwise they are included below just for reference)
    column_defs = [

        # the uniprot_id
        {
            'query_name': 'id',
            'output_name': 'Entry',
            'final_name': 'uniprot_id',
        },

        # a primary descriptive protein name,
        # followed by one or more synonymous descriptive protein names in parentheses
        {
            'query_name': 'protein names',
            'output_name': 'Protein names',
        },

        # comma-separed list of descriptive protein families
        {
            'query_name': 'families',
            'output_name': 'Protein families',
        },

        # space-separated list of all gene name synonyms for the gene encoding the protein
        {
            'query_name': 'genes',
            'output_name': 'Gene names',
        },

        # paragraph-like description of the protein's function
        {
            'query_name': 'comment(FUNCTION)',
            'output_name': 'Function [CC]',
            'final_name': 'annotation'
        },
    ]

    params = {
        'sort': 'score',
        'format': 'tab',
        'limit': str(limit),
        'query': f'organism:9606+AND+{query}',
        'columns': ','.join([column_def['query_name'] for column_def in column_defs]),
    }

    if only_reviewed:
        params['query'] += '+AND+reviewed:yes'

    try:
        response = requests.get(url, params)
    except Exception:
        logger.warning('Error while querying UniprotKB for %s' % query)
        return None

    if not response.text:
        logger.warning("No UniprotKB results found for query '%s'" % query)
        return None

    df = pd.read_csv(io.StringIO(response.text), sep='\t')

    # rename columns
    final_column_names = {
        column_def['output_name']: column_def['final_name']
        for column_def in column_defs if column_def.get('final_name')
    }
    df.rename(columns=final_column_names, inplace=True)

    # clean up all remaining column names
    columns = {
        column: (
            column
            .replace('(', '')
            .replace(' )', '')
            .replace('  ', ' ')
            .replace(' ', '_')
            .lower()
        ) for column in df.columns
    }
    df.rename(columns=columns, inplace=True)
    return df


def uniprot_id_mapper(input_ids, input_type, output_type):
    '''
    Map a list of ids from one type to another using Uniprot's ID mapping API

    Parameters
    ----------
    input_type, output_type : str, the types of the input and output ids,
        according to the abbrevations defined by uniprot here:
        https://www.uniprot.org/help/api_idmapping

    Returns
    -------
    dataframe with two columns named `input_type` and `output_type`

    Example
    -------
    To map ENST IDs to uniprot IDs:
    uniprot_id_mapper(enst_ids, input_type='ENSEMBL_TRS_ID', output_type='ACC')

    To map Uniprot IDs to ENSG IDs:
    uniprot_id_mapper(uniprot_ids, input_type='ACC', output_type='ENSEMBL_ID')

    '''
    api_url = 'https://www.uniprot.org/uploadlists'

    params = {
        'from': input_type,
        'to': output_type,
        'format': 'tab',
        'query': '',
    }

    # the number of times to try making each request
    # (the API seems to be unreliable and occasionally times out)
    max_num_tries = 9

    # the number of ids to query in each API request
    batch_size = 100

    dfs = []
    for ind in range(0, len(input_ids), batch_size):

        # the API excepts a space-separated list of ids
        params['query'] = ' '.join(input_ids[ind:(ind + batch_size)])

        df = None
        num_tries = 0
        while num_tries <= max_num_tries:
            num_tries += 1
            try:
                response = requests.get(api_url, params=params)
            except Exception:
                continue
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text), sep='\t')
                break

        if df is not None:
            dfs.append(df)
        else:
            raise Exception('Uniprot API timed out at batch %s' % ind)

    ids = pd.concat(dfs, axis=0)
    ids.rename(columns={'From': input_type, 'To': output_type}, inplace=True)
    return ids


def map_uniprot_to_ensg_using_uniprot(uniprot_id):
    '''
    Use the uniprot mapping API to look up the ensg_id for a uniprot_id
    '''
    try:
        df = uniprot_id_mapper([uniprot_id], input_type='ACC', output_type='ENSEMBL_ID')
    except Exception:
        logger.warning("Uniprot mapper API error for uniprot_id '%s'" % uniprot_id)
        return None

    if not df.shape[0]:
        logger.warning("No hits from the Uniprot mapper API for '%s'" % uniprot_id)
        return None

    retrieved_uniprot_id = df.iloc[0].ACC
    if retrieved_uniprot_id != uniprot_id:
        logger.warning(
            "The top hit from the Uniprot mapper API for '%s' has a different uniprot_id"
            % uniprot_id
        )
        return None

    ensg_id = df.iloc[0].ENSEMBL_ID
    return ensg_id


def map_uniprot_to_ensg_using_mygene(uniprot_id):
    '''
    Use the MyGene API to look up the ensg_id for a uniprot_id
    '''
    params = {
        'q': uniprot_id,
        'species': 'human',
        'ensemblonly': 'true',
        'fields': 'ensembl.gene,uniprot',
    }

    try:
        response = requests.get('http://mygene.info/v3/query', params)
    except Exception:
        logger.warning("MyGene API error for uniprot_id '%s'" % uniprot_id)
        return None

    payload = response.json()
    hits = payload.get('hits')
    if hits is None or not len(hits):
        logger.warning("No hits from the MyGene API for uniprot_id '%s'" % uniprot_id)
        return None
    hit = hits[0]

    # check that the uniprot_id of the hit matches the query uniprot_id
    # (note that, rarely, a hit can either include multiple uniprot_ids
    # or have no 'uniprot' field at all)
    hit_uniprot = hit.get('uniprot')
    if hit_uniprot is not None:
        swissprot_ids = hit_uniprot.get('Swiss-Prot') or []
        trembl_ids = hit_uniprot.get('TrEMBL') or []
        if isinstance(swissprot_ids, str):
            swissprot_ids = [swissprot_ids]
        if isinstance(trembl_ids, str):
            trembl_ids = [trembl_ids]

        if uniprot_id not in (swissprot_ids + trembl_ids):
            logger.warning(
                "The top MyGene hit for uniprot_id '%s' has a different uniprot_id"
                % uniprot_id
            )
            return None
    else:
        logger.warning(
            "No uniprot_ids in the top MyGene hit for uniprot_id '%s'"
            % uniprot_id
        )
        return None

    hit_ensembl = hit['ensembl']
    if isinstance(hit_ensembl, list):
        logger.warning(
            "Using the first of %s ensg_ids in the top MyGene hit for uniprot_id '%s'"
            % (len(hit_ensembl), uniprot_id)
        )
        hit_ensembl = hit_ensembl[0]
    ensg_id = hit_ensembl.get('gene')
    return ensg_id
