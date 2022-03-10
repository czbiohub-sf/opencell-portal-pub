import re
import json
import numpy as np
import pandas as pd

from opencell.database import uniprot_utils
from opencell.imaging.processors import FOVProcessor


def generate_cell_line_payload(cell_line, included_fields):
    '''
    The JSON payload returned by the /lines endpoint of the API
    Note that, awkwardly, the RNAseq data is a column in the crispr_design table

    included_fields : a list of optional fields to include
    '''
    design = cell_line.crispr_design

    # top-level metadata
    metadata_payload = {
        'cell_line_id': cell_line.id,
        'sort_count': cell_line.sort_count,
        'well_id': design.well_id,
        'plate_id': design.plate_design_id,
        'target_name': design.target_name,
        'target_family': design.target_family,
        'target_terminus': design.target_terminus.value[0],
        'protospacer_sequence': design.protospacer_sequence,
        'enst_id': design.enst_id,
        'ensg_id': design.ensg_id,
    }

    # TODO: merge this with top-level metadata above
    uniprot_metadata_payload = {
        'uniprot_id': design.uniprot_id,
        'gene_name': design.hgnc_metadata.symbol,
        'protein_name': uniprot_utils.prettify_hgnc_protein_name(design.hgnc_metadata.name),
    }

    abundance_payload = generate_abundance_measurement_payload(
        design.hgnc_metadata.abundance_measurements
    )

    # the FACS area and relative median log intensity
    facs_payload = {}
    if cell_line.facs_dataset:
        facs_payload = {
            'area': cell_line.facs_dataset.scalars.get('area'),
            'intensity': cell_line.facs_dataset.scalars.get('rel_median_log')
        }

    sequencing_payload = {}
    if cell_line.sequencing_dataset:
        sequencing_payload = cell_line.sequencing_dataset.scalars

    # all of the manual annotation categories
    categories = cell_line.annotation.categories if cell_line.annotation else []
    annotation_payload = {
        'categories': categories or None,
        'has_graded_annotations': bool(np.any([
            re.match('.*_[1,2,3]$', cat) is not None for cat in categories
        ]))
    }

    # the id of the 'best' pulldown
    pulldown = cell_line.get_best_pulldown()
    pulldown_id = pulldown.id if pulldown else None

    payload = {
        'metadata': metadata_payload,
        'facs': facs_payload,
        'sequencing': sequencing_payload,
        'uniprot_metadata': uniprot_metadata_payload,
        'abundance_data': abundance_payload,
        'annotation': annotation_payload,
        'best_pulldown': {'id': pulldown_id},
    }

    # get the thumbnail of the annotated ROI from the 'best' FOV
    if 'best-fov' in included_fields:
        fov = cell_line.get_best_fov()
        if fov and fov.rois:
            # hack: assume there is only one ROI (the annotated ROI)
            thumbnail = fov.rois[0].get_thumbnail()
            payload['best_fov'] = {
                'thumbnails': thumbnail.as_dict() if thumbnail else None
            }
    return payload


def generate_facs_payload(facs_dataset):
    '''
    '''
    return {'histograms': facs_dataset.simplify_histograms()}


def generate_abundance_measurement_payload(abundance_measurements):

    abundance_payload = {}
    if not abundance_measurements:
        return None

    # TODO: better logic to select the best measurement
    abundance = abundance_measurements[0]

    # RNA-seq expression is always measured (but may be zero)
    abundance_payload['rna_abundance'] = abundance.measured_transcript_expression

    # protein abundance is either measured or imputed
    protein_concentration = abundance.measured_protein_concentration
    if pd.isna(protein_concentration):
        protein_concentration = abundance.imputed_protein_concentration
        abundance_payload['protein_abundance_imputed'] = True

    abundance_payload['protein_concentration'] = protein_concentration
    abundance_payload['protein_copy_number'] = abundance.calc_protein_copy_number(
        protein_concentration
    )

    # coerce nans to None
    abundance_payload = json.loads(pd.Series(abundance_payload).to_json())

    return abundance_payload


def generate_fov_payload(fov, include_rois=False, include_thumbnails=False):
    '''
    The JSON payload for an FOV (and its ROIs)
    '''

    # basic metadata
    metadata = {
        'id': fov.id,
        'score': fov.get_score(),
        'pml_id': fov.dataset.pml_id,
        'src_filename': fov.raw_filename,
        'z_step_size': FOVProcessor.z_step_size(fov.dataset.pml_id),
    }

    # the 488 exposure settings
    tiff_metadata = fov.get_result('raw-tiff-metadata')
    if tiff_metadata:
        metadata['laser_power_488'] = tiff_metadata.data.get('laser_power_488_488')
        metadata['exposure_time_488'] = tiff_metadata.data.get('exposure_time_488')
        metadata['max_intensity_488'] = tiff_metadata.data.get('max_intensity_488')

    # the position of the cell layer center, relative to the bottom of the stack
    tiff_metadata = fov.get_result('clean-tiff-metadata')
    if tiff_metadata and tiff_metadata.data.get('cell_layer_center') is not None:
        metadata['cell_layer_center'] = (
            tiff_metadata.data.get('cell_layer_center')*metadata['z_step_size']
        )

    fov_payload = {
        'metadata': metadata,
        'annotation': fov.annotation.as_dict() if fov.annotation else None
    }

    # assume there's only one annotated ROI per FOV, and always include the ROI thumbnail
    # (also assume that there's only one thumbnail per ROI)
    if include_rois and fov.rois:
        roi = fov.rois[0]
        roi_payload = roi.as_dict()
        roi_payload['thumbnail'] = roi.get_thumbnail().as_dict()
        fov_payload['rois'] = [roi_payload]

    if include_thumbnails:
        thumbnail = fov.get_thumbnail()
        fov_payload['thumbnails'] = thumbnail.as_dict() if thumbnail else None

    return fov_payload


def generate_pulldown_hits_payload(pulldown, significant_hits, nonsignificant_hits):
    '''
    The JSON payload for a mass spec pulldown and all of its hits

    pulldown : a models.MassSpecPulldown instance
    significant_hits : a list of models.MassSpecHit instances corresponding to
        the pulldown's significant hits
    nonsignificant_hits : a list of tuples of (pval, enrichment)
        for all of the pulldown's non-significant hits (usually thousands)
    '''

    hit_attrs = ['pval', 'enrichment', 'interaction_stoich', 'abundance_stoich', 'is_minor_hit']
    significant_hit_payloads = []
    for hit in significant_hits:
        significant_hit_payload = {attr: getattr(hit, attr) for attr in hit_attrs}
        significant_hit_payload.update(
            generate_protein_group_payload(
                hit.protein_group, pulldown.cell_line.crispr_design_id
            )
        )
        significant_hit_payloads.append(significant_hit_payload)

    # hackish way to coerce NaNs and Infs to None
    significant_hit_payloads = json.loads(
        pd.DataFrame(data=significant_hit_payloads).to_json(orient='records')
    )

    # compress the nonsignificant hits by dropping digits
    nonsignificant_hit_payloads = [
        [float('%0.3f' % pval), float('%0.3f' % enrichment)]
        for pval, enrichment in nonsignificant_hits
    ]

    pulldown_hits_payload = {
        'metadata': pulldown.as_dict(),
        'significant_hits': significant_hit_payloads,
        'nonsignificant_hits': nonsignificant_hit_payloads
    }
    return pulldown_hits_payload


def generate_protein_group_payload(protein_group, pulldown_crispr_design_id=None):
    '''
    Construct the payload to represent a protein group

    pulldown_crispr_design_id : optional id of the crispr design of the target
    from which the pulldown came
    '''

    # the 'primary' gene name for each uniprot_id in the protein group
    gene_names = ['Unknown']
    if protein_group.manual_gene_name:
        gene_names = protein_group.manual_gene_name.split(', ')
    elif protein_group.hgnc_metadata:
        gene_names = sorted(set([d.symbol for d in protein_group.hgnc_metadata]))

    ensg_ids = [d.ensg_id for d in protein_group.hgnc_metadata]

    # the target names of the crispr designs that are associated with this protein group
    # (these are not always unique, because there are multiple designs for some targets)
    target_names = list(set([design.target_name for design in protein_group.crispr_designs]))

    payload = {
        # TODO: rename this because the gene_names are not from uniprot anymore
        'uniprot_gene_names': gene_names,
        'opencell_target_names': target_names,
        'ensg_ids': ensg_ids,
    }

    # use the crispr_design_id of the pulldown to determine
    # whether this protein group corresponds to the pulldown's bait
    if pulldown_crispr_design_id is not None:
        design_ids = [design.id for design in protein_group.crispr_designs]
        payload['is_bait'] = pulldown_crispr_design_id in design_ids

    return payload
