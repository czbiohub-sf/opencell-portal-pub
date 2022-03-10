import logging
import pandas as pd
import numpy as np
from opencell.database import models, utils, uniprot_utils

logger = logging.getLogger(__name__)


def insert_uniprot_metadata_from_id(session, uniprot_id):
    '''
    Retrieve and insert Uniprot metadata for a given uniprot_id

    Note that we set limit=10 because the correct result for the query uniprot_id
    is sometimes not the top (i.e., first) result from the uniprotkb query
    '''
    metadata = uniprot_utils.query_uniprotkb(query=uniprot_id, only_reviewed=False, limit=10)
    if metadata is None:
        logger.warning('No UniprotKB results were found for uniprot_id %s' % uniprot_id)
        return

    # filter out results corresponding to other uniprot_ids
    # (this is necessary because we use limit=10 above, and because, sometimes,
    # one or more results are retrieved, but none of them actually match the query uniprot_id)
    metadata = metadata.loc[metadata.uniprot_id == uniprot_id]
    if not len(metadata):
        logger.warning(
            'UniprotKB results were retrieved for uniprot_id %s '
            'but none have the correct uniprot_id'
            % uniprot_id
        )
        return

    uniprot_metadata = models.UniprotMetadata(**metadata.iloc[0])
    utils.add_and_commit(session, uniprot_metadata)


def insert_uniprot_metadata_for_crispr_design(session, crispr_design_id, retrieved_metadata=None):
    '''
    Retrieve and insert the raw uniprot metadata for a crispr design

    Parameters
    ----------
    crispr_design_id : int, required
        the id of the crispr design for which to insert uniprot metadata
    retrieved_metadata : one-row pd.Dataframe, optional
        The raw uniprot metadata corresponding to the crispr design
        (intended for edge cases in which the correct metadata must be manually specified,
        rather than retrieved by uniprot_utils.get_uniprot_metadata)
    '''
    crispr_design = (
        session.query(models.CrisprDesign)
        .filter(models.CrisprDesign.id == crispr_design_id)
        .one()
    )
    if crispr_design.uniprot_id is not None:
        return

    # retrieve the metadata for the crispr design from the UniprotKB API
    if retrieved_metadata is None:

        # first try querying with the ENST ID, if one was provided
        if crispr_design.enst_id is not None:
            retrieved_metadata = uniprot_utils.query_uniprotkb(
                query=crispr_design.enst_id, limit=1
            )

        # if there is no ENST ID or no metadata was found, query with the target name
        if crispr_design.enst_id is None or retrieved_metadata is None:
            logger.warning(
                "Querying UniprotKB by target name and not by ENST ID for target '%s'"
                % crispr_design.target_name
            )
            retrieved_metadata = uniprot_utils.query_uniprotkb(
                query=crispr_design.target_name, limit=1
            )

    if retrieved_metadata is None:
        logger.warning('No Uniprot metadata found for target %s' % crispr_design.target_name)
        return
    retrieved_metadata = retrieved_metadata.iloc[0]

    # check whether the retrieved metadata already exists
    extant_metadata = (
        session.query(models.UniprotMetadata)
        .filter(models.UniprotMetadata.uniprot_id == retrieved_metadata.uniprot_id)
        .one_or_none()
    )
    if extant_metadata is None:
        logger.info(
            'Inserting uniprot metadata for new uniprot_id %s' % retrieved_metadata.uniprot_id
        )
        uniprot_metadata = models.UniprotMetadata(**retrieved_metadata)
        utils.add_and_commit(session, uniprot_metadata)

    # update the crispr design's uniprot_id
    crispr_design.uniprot_id = retrieved_metadata.uniprot_id
    utils.add_and_commit(session, crispr_design)
