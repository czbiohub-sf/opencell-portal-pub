import flask
import imageio
import io
import json
import os
import pandas as pd
import sqlalchemy as sa
import tifffile
import urllib

from flask_restful import Resource

from opencell.imaging import utils
from opencell.api import payloads, cytoscape_payload
from opencell.api.cache import cache
from opencell.database import models, metadata_operations, uniprot_utils
from opencell.database import utils as db_utils
from opencell.imaging.processors import FOVProcessor


# copied from https://stackoverflow.com/questions/24816799/how-to-use-flask-cache-with-flask-restful
def cache_key():
    args = flask.request.args
    key = flask.request.path + '?' + urllib.parse.urlencode([
        (k, v) for k in sorted(args) for v in sorted(args.getlist(k))
    ])
    return key


class ClearCache(Resource):
    def get(self):
        with flask.current_app.app_context():
            cache.clear()
        return flask.jsonify({'result': 'cache cleared'})


class GeneNameSearch(Resource):
    '''
    A list of cell_line_ids and ensg_ids that exactly correspond to a gene name
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, gene_name):
        payload = {}
        gene_name = gene_name.upper()

        publication_ready_only = flask.request.args.get('publication_ready') == 'true'
        if flask.current_app.config['HIDE_PRIVATE_DATA']:
            publication_ready_only = True

        # search for opencell targets
        query = (
            flask.current_app.Session.query(models.CellLine)
            .join(models.CellLine.crispr_design)
            .filter(sa.func.upper(models.CrisprDesign.target_name) == gene_name)
        )

        if publication_ready_only:
            cell_line_ids = metadata_operations.get_lines_by_annotation(
                engine=flask.current_app.Session.get_bind(), annotation='publication_ready'
            )
            query = query.filter(models.CellLine.id.in_(cell_line_ids))

        # hack for the positive controls
        if gene_name in ['CLTA', 'BCAP31']:
            query = query.filter(models.CrisprDesign.plate_design_id == 'P0001')

        targets = query.all()

        # use a zero-padded 11-digit number to match ENSG ID format
        if targets:
            payload['oc_ids'] = ['OPCT%011d' % target.id for target in targets]

        # search the gene names column in the uniprot metadata table
        # (use `ilike` for case-insensitivity)
        hgnc_entries = pd.read_sql(
            '''
            select ensg_id from hgnc_metadata where %(query)s ilike symbol
            ''',
            flask.current_app.Session.get_bind(),
            params=dict(query=gene_name)
        )
        if len(hgnc_entries):
            payload['ensg_ids'] = list(set(hgnc_entries.ensg_id))

        return flask.jsonify(payload)


class FullTextSearch(Resource):
    '''
    Full-text search of all opencell targets and interactors

    This is conducted in two steps:
    First, a full-text search of the uniprot protein_names field is attempted;
    this will only yield results if the query is some common word or phrase
    (e.g., 'actin', 'membrane', 'nuclear lamina', etc).

    If this search finds no results, we assume the query is a portion of a gene name,
    and we search the uniprot gene_names field for all gene names
    that start with, or exactly match, the query.

    NOTE: the queries in this method rely on a materialized view
    called 'searchable_hgnc_metadata' defined in `define_views.sql`
    '''
    @staticmethod
    def get_approved_gene_name_from_query(session, query):
        '''
        '''
        query_is_valid_gene_name = False
        query_is_legacy_gene_name = False
        approved_gene_name = None

        # first determine if the query is an exact HGNC-approved gene name
        exact_matches = (
            session.query(models.HGNCMetadata)
            .filter(models.HGNCMetadata.symbol == query.upper())
            .one_or_none()
        )
        query_is_valid_gene_name = exact_matches is not None
        if query_is_valid_gene_name:
            approved_gene_name = query.upper()

        # check if the query is an exact legacy gene name
        else:
            result = pd.read_sql(
                '''
                select * from (
                    select symbol, ensg_id, unnest(
                        string_to_array(prev_symbol, '|') || string_to_array(alias_symbol, '|')
                    ) as alias_or_prev
                    from hgnc_metadata
                ) tmp
                where alias_or_prev ilike %(query)s
                ''',
                session.get_bind(),
                params=dict(query=query.upper())
            )
            if len(result):
                query_is_legacy_gene_name = True
                approved_gene_name = result.iloc[0].symbol

        return query_is_valid_gene_name, query_is_legacy_gene_name, approved_gene_name


    @staticmethod
    def search_protein_names(engine, query):
        '''
        Full-text search of uniprot protein names for all opencell targets and interactors
        (this relies on a materialized view called searchable_hgnc_metadata)
        '''
        results = pd.read_sql(
            '''
            select * from (
                select *, ts_rank_cd(content, query) as relevance
                from searchable_hgnc_metadata, plainto_tsquery(%(query)s) as query
                where content @@ query
            ) as hits
            order by relevance desc;
            ''',
            engine,
            params=dict(query=query)
        )
        return results


    @staticmethod
    def search_gene_names(engine, query):
        '''
        Search for opencell targets and interactors any of whose HGNC gene names
        (current, previous, or alias) starts with the query
        '''
        results = pd.read_sql(
            '''
            select * from searchable_hgnc_metadata
            where ensg_id in (
                select ensg_id from (
                    select ensg_id,
                        unnest(
                            string_to_array(symbol, '')
                            || string_to_array(prev_symbol, '|')
                            || string_to_array(alias_symbol, '|')
                        ) as gene_name
                    from hgnc_metadata
                ) as tmp
                where gene_name like %(query)s
            );
            ''',
            engine,
            params=dict(query=('%s%%' % query.upper()))
        )
        # there's no way of ranking these results, so we create a relevance column
        # with a relevance greater than the maximum relevance
        # returned by ts_rank_cd in `search_protein_names`
        results['relevance'] = 1.0
        return results


    @cache.cached(key_prefix=cache_key)
    def get(self, query):
        engine = flask.current_app.Session.get_bind()

        # eliminate trailing spaces
        query = query.strip()

        # attempt to look up the approved gene name from the query,
        # in the even that the query is an exact alias or previous gene name
        (
            query_is_valid_gene_name, query_is_legacy_gene_name, approved_gene_name
        ) = self.get_approved_gene_name_from_query(flask.current_app.Session, query)

        # search for partial gene name matches
        partial_gene_name_matches = self.search_gene_names(engine, query)

        # if there are no partial matches but the query is an exact legacy gene name,
        # try again using the approved gene name
        if query_is_legacy_gene_name and not partial_gene_name_matches.shape[0]:
            partial_gene_name_matches = self.search_gene_names(engine, approved_gene_name)

        # always search the protein names with the original query
        protein_name_matches = self.search_protein_names(engine, query)

        # combine the results from both searches
        all_results = pd.concat((partial_gene_name_matches, protein_name_matches), axis=0)

        # eliminate duplicates
        all_results = all_results.groupby('ensg_id').first().reset_index()

        # hackish logic that determines whether the result is a target, interactor, or expressed
        all_results['status'] = 'unknown'
        for ind, row in all_results.iterrows():
            if not pd.isna(row.published_cell_line_id):
                status = 'Target'
            elif not pd.isna(row.significant_protein_group_id):
                status = 'Interactor'
            elif not pd.isna(row.measured_expression):
                status = 'Expressed'
            else:
                # the space prefix here is a deliberate hack to force undetected proteins
                # to appear last when the search results are sorted by status in the frontend
                status = ' Not detected'
            all_results.at[ind, 'status'] = status

        # force the targets to the top of the search results, then sort by relevance
        all_results.sort_values(['status', 'relevance'], inplace=True, ascending=False)

        # prettify the protein names
        all_results['protein_name'] = all_results.protein_name.apply(
            lambda s: uniprot_utils.prettify_hgnc_protein_name(s)
        )

        # drop unneeded column
        all_results.drop(labels=['content', 'significant_protein_group_id'], axis=1, inplace=True)

        # if the query was a valid (approved or legacy) gene name,
        # set the relevance of its exact match, if there was one, to 10
        exact_match_found = False
        if approved_gene_name is not None:
            mask = all_results.gene_name.apply(lambda names: approved_gene_name in names)
            all_results.loc[mask, 'relevance'] = 10
            exact_match_found = bool(mask.sum() > 0)

        return flask.jsonify({
            'is_valid_gene_name': query_is_valid_gene_name,
            'is_legacy_gene_name': query_is_legacy_gene_name,
            'approved_gene_name': approved_gene_name,
            'exact_match_found': exact_match_found,
            'hits': json.loads(all_results.to_json(orient='records')),
        })


class UniProtKBAnnotation(Resource):
    '''
    The prettified functional annotation from UniProtKB
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, uniprot_id):
        metadata = (
            flask.current_app.Session.query(models.UniprotKBMetadata)
            .filter(models.UniprotKBMetadata.primary_uniprot_id == uniprot_id)
            .one_or_none()
        )
        if metadata is None:
            return flask.abort(404, 'No UniProtKB entry for uniprot_id %s' % uniprot_id)

        return flask.jsonify(
            {
                'uniprot_id': uniprot_id,
                'functional_annotation': uniprot_utils.prettify_uniprot_annotation(
                    metadata.function_comment
                ),
            }
        )


class AbundanceDataset(Resource):
    '''
    The full abundance dataset
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self):
        df = pd.read_sql(
            '''
            select measured_transcript_expression as rna, measured_protein_concentration as pro
            from abundance_measurement
            where measured_protein_concentration is not null
                and measured_protein_concentration != 'NaN'::NUMERIC
                and random() < 0.3
            ''',
            flask.current_app.Session.get_bind()
        )
        return flask.jsonify(json.loads(df.to_json(orient='records')))


class TargetNames(Resource):
    '''
    A list of the target names and HGNC protein names for all crispr designs
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self):

        publication_ready_only = flask.request.args.get('publication_ready') == 'true'
        if flask.current_app.config['HIDE_PRIVATE_DATA']:
            publication_ready_only = True

        cell_line_ids = None
        if publication_ready_only:
            cell_line_ids = metadata_operations.get_lines_by_annotation(
                engine=flask.current_app.Session.get_bind(), annotation='publication_ready'
            )

        query = (
            flask.current_app.Session.query(
                models.CrisprDesign.target_name,
                models.HGNCMetadata.name.label('protein_name'),
            )
            .join(models.CrisprDesign.hgnc_metadata)
        )
        if cell_line_ids is not None:
            query = (
                query.join(models.CrisprDesign.cell_lines)
                .filter(models.CellLine.id.in_(cell_line_ids))
            )

        names = pd.DataFrame(data=[row._asdict() for row in query.all()])

        # eliminate duplicates
        names = names.groupby('target_name').first().reset_index()

        return flask.jsonify(json.loads(names.to_json(orient='records')))


class Plate(Resource):

    def get(self, plate_id):
        plate = (
            flask.current_app.Session.query(models.PlateDesign)
            .filter(models.PlateDesign.design_id == plate_id)
            .one_or_none()
        )
        targets = [d.target_name for d in plate.crispr_designs]
        return {
            'plate_id': plate.design_id,
            'targets': targets,
        }


class CellLines(Resource):
    '''
    A list of cell line metadata for all cell lines,
    possibly filtered by plate_id and the publication_ready annotation
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self):

        Session = flask.current_app.Session

        args = flask.request.args
        plate_id = args.get('plate_id')
        publication_ready_only = args.get('publication_ready') == 'true'

        if flask.current_app.config['HIDE_PRIVATE_DATA']:
            publication_ready_only = True

        included_fields = args.get('fields')
        included_fields = included_fields.split(',') if included_fields else []

        cell_line_ids = args.get('ids')
        cell_line_ids = [int(_id) for _id in cell_line_ids.split(',')] if cell_line_ids else []

        if publication_ready_only:
            pr_cell_line_ids = metadata_operations.get_lines_by_annotation(
                engine=flask.current_app.Session.get_bind(), annotation='publication_ready'
            )
            if len(cell_line_ids):
                cell_line_ids = list(set(cell_line_ids).intersection(pr_cell_line_ids))
            else:
                cell_line_ids = pr_cell_line_ids

        # cell line query with the eager-loading required by generate_cell_line_payload
        query = (
            Session.query(models.CellLine)
            .join(models.CellLine.crispr_design)
            .options(
                (
                    sa.orm.joinedload(models.CellLine.crispr_design, innerjoin=True)
                    .joinedload(models.CrisprDesign.hgnc_metadata, innerjoin=True)
                    .joinedload(models.HGNCMetadata.abundance_measurements)
                ), (
                    sa.orm.joinedload(models.CellLine.crispr_design, innerjoin=True)
                    .joinedload(models.CrisprDesign.uniprotkb_metadata, innerjoin=True)
                ),
                sa.orm.joinedload(models.CellLine.facs_dataset),
                sa.orm.joinedload(models.CellLine.sequencing_dataset),
                sa.orm.joinedload(models.CellLine.annotation),
                sa.orm.joinedload(models.CellLine.pulldowns)
            )
        )

        if plate_id:
            query = query.filter(models.CrisprDesign.plate_design_id == plate_id)
        if cell_line_ids:
            query = query.filter(models.CellLine.id.in_(cell_line_ids))

        if 'best-fov' in included_fields:
            query = query.options(
                (
                    sa.orm.joinedload(models.CellLine.fovs, innerjoin=True)
                    .joinedload(models.MicroscopyFOV.rois, innerjoin=True)
                    .joinedload(models.MicroscopyFOVROI.thumbnails, innerjoin=True)
                ), (
                    sa.orm.joinedload(models.CellLine.fovs, innerjoin=True)
                    .joinedload(models.MicroscopyFOV.annotation, innerjoin=True)
                )
            )

        lines = query.all()

        # a separate query for counting FOVs and annotated FOVs per cell line
        fov_counts_query = (
            Session.query(
                models.CellLine.id,
                sa.func.count(models.MicroscopyFOV.id).label('num_fovs'),
                sa.func.count(models.MicroscopyFOVAnnotation.id).label('num_annotated_fovs'),
            )
            .outerjoin(models.CellLine.fovs)
            .outerjoin(models.MicroscopyFOV.annotation)
            .filter(models.CellLine.id.in_([line.id for line in lines]))
            .group_by(models.CellLine.id)
        )
        fov_counts = pd.DataFrame([row._asdict() for row in fov_counts_query.all()])

        # hackish counting of the number of annotated FOVs from dragonfly-automation datasets
        # (the 'dad' appendix stands for dragonfly-automation datasets)
        dad_pmls = ['PML%04d' % ind for ind in range(196, 999)]
        fov_counts_query = fov_counts_query.filter(models.MicroscopyFOV.pml_id == sa.any_(dad_pmls))
        fov_counts_dad = pd.DataFrame([row._asdict() for row in fov_counts_query.all()])
        fov_counts_dad.rename(
            columns={column: '%s_dad' % column for column in fov_counts_dad.columns},
            inplace=True
        )
        if fov_counts_dad.shape[0]:
            fov_counts = pd.merge(
                fov_counts, fov_counts_dad, left_on='id', right_on='id_dad', how='left'
            )

        # the list of pulldown_ids with saved cytoscape networks
        pulldowns_with_saved_networks = [
            row[0] for row in Session.query(models.MassSpecPulldownNetwork.pulldown_id).all()
        ]

        cell_line_payloads = []
        for line in lines:
            payload = payloads.generate_cell_line_payload(line, included_fields)

            # append the FOV counts (for the internal version of the frontend)
            fov_count = fov_counts.loc[fov_counts.id == line.id].iloc[0]
            if fov_count.shape[0]:
                payload['fov_counts'] = json.loads(fov_count.to_json())

            # append a flag for the existence of a saved pulldown network
            pulldown_id = payload['best_pulldown']['id']
            if pulldown_id is not None:
                payload['best_pulldown']['has_saved_network'] = (
                    pulldown_id in pulldowns_with_saved_networks
                )

            cell_line_payloads.append(payload)

        return flask.jsonify(cell_line_payloads)


class CellLineResource(Resource):

    def parse_listlike_arg(self, name, allowed_values, sep=','):
        '''
        Parse and validate a list-like URL parameter
        '''
        error = None
        arg = flask.request.args.get(name)
        values = arg.split(sep) if arg else []
        if not set(values).issubset(allowed_values):
            error = flask.abort(404, 'Invalid value passed to the %s parameter' % name)
        return values, error

    @staticmethod
    def get_cell_line(cell_line_id):
        return (
            flask.current_app.Session.query(models.CellLine)
            .filter(models.CellLine.id == cell_line_id)
            .one_or_none()
        )


class CellLine(CellLineResource):
    '''
    The cell line metadata for a single cell line
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, cell_line_id):
        line = self.get_cell_line(cell_line_id)
        optional_fields, error = self.parse_listlike_arg('fields', allowed_values=['best-fov'])
        if error:
            return error
        payload = payloads.generate_cell_line_payload(line, optional_fields)
        return flask.jsonify(payload)


class InteractorResource(Resource):

    @classmethod
    def get_protein_groups(cls, ensg_id):
        '''
        Get all of the significant protein groups associated with the ENSG ID
        '''
        protein_groups = (
            flask.current_app.Session.query(models.MassSpecProteinGroup)
            .join(models.ProteinGroupEnsemblAssociation)
            .filter(models.ProteinGroupEnsemblAssociation.ensg_id == ensg_id)
            .options(sa.orm.joinedload(models.MassSpecProteinGroup.hgnc_metadata))
            .all()
        )
        return protein_groups

    @classmethod
    def construct_metadata(cls, ensg_id):
        '''
        Generates the metadata object for an ENSG ID,
        following the schema of the cell line metadata (see payloads.generate_cell_line_payload)
        '''
        payload = {}

        hgnc_metadata = (
            flask.current_app.Session.query(models.HGNCMetadata)
            .options(sa.orm.joinedload(models.HGNCMetadata.uniprotkb_metadata, innerjoin=True))
            .options(sa.orm.joinedload(models.HGNCMetadata.abundance_measurements))
            .filter(models.HGNCMetadata.ensg_id == ensg_id)
            .one_or_none()
        )
        protein_groups = cls.get_protein_groups(ensg_id)

        abundance_payload = payloads.generate_abundance_measurement_payload(
            hgnc_metadata.abundance_measurements
        )
        payload['abundance_data'] = abundance_payload

        # TODO: a better way to pick the best uniprot_id from which to construct the metadata
        # (that is, from which to take the functional annotation)
        uniprotkb_metadata = hgnc_metadata.uniprotkb_metadata[0]

        # HACK: this is copied from the cell_line payload
        payload['uniprot_metadata'] = {
            'uniprot_id': uniprotkb_metadata.primary_uniprot_id,
            'protein_name': uniprot_utils.prettify_hgnc_protein_name(hgnc_metadata.name),
            'annotation': uniprot_utils.prettify_uniprot_annotation(
                uniprotkb_metadata.function_comment
            ),
        }

        # generic ensg-level metadata (mimics the cell_line 'metadata' field)
        payload['metadata'] = {
            'ensg_id': ensg_id,
            'target_name': hgnc_metadata.symbol,
            'has_interactors': protein_groups is not None and len(protein_groups) > 0,
            'is_expressed': (
                abundance_payload is not None and abundance_payload['rna_abundance'] > 0
            ),
        }
        return payload


class InteractorMetadata(InteractorResource):
    '''
    The metadata for an 'interactor'
    (note that the 'interactor' nomenclature is misleading;
    this is any gene in the genome, identified by an ensg_id)
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, ensg_id):
        payload = self.construct_metadata(ensg_id)
        return flask.jsonify(payload)


class InteractorNetwork(InteractorResource):
    '''
    The cytoscape interaction network for an interactor (identified by an ensg_id)
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, ensg_id):

        protein_groups = self.get_protein_groups(ensg_id)
        if not protein_groups:
            return flask.abort(404, 'There are no protein groups for ENSG ID %s' % ensg_id)

        interacting_pulldowns = []
        for protein_group in protein_groups:
            interacting_pulldowns.extend(protein_group.get_pulldowns())

        # TODO: refactor construct_network so we do not have to pass a single primary protein group
        primary_protein_group = protein_groups[0]
        nodes, edges = cytoscape_payload.construct_network(
            interacting_pulldowns=interacting_pulldowns,
            origin_protein_group=primary_protein_group,
        )

        # create compound nodes to represent superclusters and subclusters
        nodes, parent_nodes = cytoscape_payload.construct_compound_nodes(
            nodes,
            clustering_analysis_type=flask.request.args.get('clustering_analysis_type'),
            subcluster_type=flask.request.args.get('subcluster_type'),
            engine=flask.current_app.Session.get_bind()
        )
        payload = {
            'parent_nodes': [{'data': node} for node in parent_nodes],
            'nodes': [{'data': node} for node in nodes],
            'edges': [{'data': edge} for edge in edges],
            'metadata': self.construct_metadata(ensg_id)
        }
        return flask.jsonify(payload)


class FACSDataset(CellLineResource):
    @cache.cached(key_prefix=cache_key)
    def get(self, cell_line_id):
        line = self.get_cell_line(cell_line_id)
        if not line.facs_dataset:
            return flask.abort(404)
        payload = payloads.generate_facs_payload(line.facs_dataset)
        return flask.jsonify(payload)


class MicroscopyFOVMetadata(CellLineResource):
    '''
    Metadata for all of the FOVs associated with a cell line
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, cell_line_id):

        only_annotated = flask.request.args.get('annotatedonly') == 'true'

        included_fields, error = self.parse_listlike_arg(
            name='fields', allowed_values=['rois', 'thumbnails']
        )
        if error:
            return error

        line = self.get_cell_line(cell_line_id)
        query = (
            flask.current_app.Session.query(models.MicroscopyFOV)
            .options(
                sa.orm.joinedload(models.MicroscopyFOV.dataset, innerjoin=True),
                sa.orm.joinedload(models.MicroscopyFOV.results, innerjoin=True),
                sa.orm.joinedload(models.MicroscopyFOV.annotation)
            )
            .filter(models.MicroscopyFOV.cell_line_id == line.id)
        )

        if only_annotated:
            query = query.filter(models.MicroscopyFOV.annotation != None)  # noqa

        if 'rois' in included_fields:
            query = query.options(
                sa.orm.joinedload(models.MicroscopyFOV.rois, innerjoin=True)
            )

        if 'thumbnails' in included_fields:
            query = query.options(
                sa.orm.joinedload(models.MicroscopyFOV.thumbnails, innerjoin=False)
            )

        fovs = query.all()
        if not fovs:
            return flask.abort(404, 'There are no FOVs associated with the cell line')

        payload = [
            payloads.generate_fov_payload(
                fov,
                include_rois=('rois' in included_fields),
                include_thumbnails=('thumbnails' in included_fields)
            )
            for fov in fovs
        ]

        # sort by FOV score (unscored FOVs last)
        payload = sorted(payload, key=lambda row: row['metadata'].get('score') or -2)[::-1]
        return flask.jsonify(payload)


class PulldownResource(CellLineResource):

    @staticmethod
    def get_pulldown(pulldown_id):
        pulldown = (
            flask.current_app.Session.query(models.MassSpecPulldown)
            .filter(models.MassSpecPulldown.id == pulldown_id)
            .one_or_none()
        )
        if not pulldown:
            return flask.abort(404, 'Pulldown %d does not exist' % pulldown_id)
        return pulldown


class PulldownHits(PulldownResource):
    '''
    The metadata and hits for a pulldown
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, pulldown_id):
        Session = flask.current_app.Session
        pulldown = self.get_pulldown(pulldown_id)
        if not pulldown.hits:
            return flask.abort(404, 'Pulldown %s does not have any hits' % pulldown_id)

        significant_hits = pulldown.get_significant_hits()

        # we need only the pval and enrichment for the non-significant hits
        nonsignificant_hits = (
            Session.query(models.MassSpecHit.pval, models.MassSpecHit.enrichment)
            .filter(models.MassSpecHit.pulldown_id == pulldown.id)
            .filter(models.MassSpecHit.is_minor_hit == False)  # noqa
            .filter(models.MassSpecHit.is_significant_hit == False)  # noqa
            .all()
        )

        # construct the JSON payload from the pulldown and hit instances
        payload = payloads.generate_pulldown_hits_payload(
            pulldown, significant_hits, nonsignificant_hits
        )
        return flask.jsonify(payload)


class PulldownNetwork(PulldownResource):
    '''
    The cytoscape interaction network for a pulldown
    (see comments in cytoscape_payload.construct_network for details)
    '''
    @cache.cached(key_prefix=cache_key)
    def get(self, pulldown_id):

        pulldown = self.get_pulldown(pulldown_id)

        # determine the primary protein group to represent the target;
        # if the target appears in its own pulldown, this is easy
        origin_protein_group = None
        bait_hit = pulldown.get_bait_hit(only_one=True)
        if bait_hit:
            origin_protein_group = bait_hit.protein_group

        # if the target does not appear in its own pulldown, we must use the protein group
        # for the ENSG ID associated with the target's crispr design
        # TODO: refactor so we can keep the full list rather than picking one protein_group
        else:
            protein_groups = InteractorResource.get_protein_groups(
                pulldown.cell_line.crispr_design.ensg_id
            )
            if protein_groups:
                origin_protein_group = protein_groups[0]

        # edge case: there is no significant protein group assoc with the target at all
        # TODO: figure out how to handle this gracefully;
        # either query for *any* PG assoc w the ensg_id, or mock a protein_group instance?
        if origin_protein_group is None:
            crispr_design = pulldown.cell_line.crispr_design
            return flask.abort(
                404,
                'There is no protein group associated with target %s (%s)'
                % (crispr_design.target_name, crispr_design.ensg_id)
            )

        # create nodes to represent direct hits and/or interacting pulldowns,
        # and the edges between them
        nodes, edges = cytoscape_payload.construct_network(
            target_pulldown=pulldown, origin_protein_group=origin_protein_group
        )

        # create compound nodes to represent superclusters and subclusters
        nodes, parent_nodes = cytoscape_payload.construct_compound_nodes(
            nodes,
            clustering_analysis_type=flask.request.args.get('clustering_analysis_type'),
            subcluster_type=flask.request.args.get('subcluster_type'),
            engine=flask.current_app.Session.get_bind()
        )

        payload = {
            'parent_nodes': [{'data': node} for node in parent_nodes],
            'nodes': [{'data': node} for node in nodes],
            'edges': [{'data': edge} for edge in edges],
            'metadata': pulldown.as_dict(),
        }

        # coerce NaNs and Infs in stoichiometries to None
        payload['nodes'] = json.loads(
            pd.DataFrame(data=payload['nodes']).to_json(orient='records')
        )

        return flask.jsonify(payload)


class PulldownClusters(PulldownResource):
    '''
    The cluster heatmap(s) in which a cell line's pulldown appears

    The cluster heatmap represents a
    '''
    def get(self, pulldown_id):
        Session = flask.current_app.Session
        pulldown = self.get_pulldown(pulldown_id)

        # get the cluster_ids of all clusters in which the pulldown appears
        rows = (
            Session.query(sa.distinct(models.MassSpecClusterHeatmap.cluster_id))
            .join(models.MassSpecClusterHeatmap.hit)
            .join(models.MassSpecHit.pulldown)
            .filter(models.MassSpecPulldown.id == pulldown.id)
            .all()
        )
        cluster_ids = [row[0] for row in rows]

        if not cluster_ids:
            return flask.abort(404, 'Pulldown %s does not appear in any clusters' % pulldown_id)

        # for now, if there are multiple clusters, pick the first one
        cluster_id = cluster_ids[0]

        # get the cluster heatmap tiles
        # (one row of the ClusterHeatmap table corresponds to one tile)
        rows = (
            Session.query(
                models.MassSpecClusterHeatmap.hit_id,
                models.MassSpecClusterHeatmap.row_index,
                models.MassSpecClusterHeatmap.col_index,
                models.MassSpecHit.pval,
                models.MassSpecHit.enrichment,
                models.MassSpecHit.interaction_stoich,
                models.MassSpecHit.abundance_stoich,
            )
            .join(models.MassSpecClusterHeatmap.hit)
            .filter(models.MassSpecClusterHeatmap.cluster_id == cluster_id)
            .all()
        )
        heatmap_tiles = pd.DataFrame(data=rows)

        # pick an arbitrary hit_id from each column and each row of the heatmap
        # we will use these hit_ids to retrieve the pulldown and protein group metadata
        # for the columns and rows, respectively, since we know/assume that all of the hits
        # in each column correspond to the same pulldown, and all of the hits in each row
        # correspond to the same protein group
        heatmap_row_metadata = heatmap_tiles.groupby('row_index').first().reset_index()
        heatmap_column_metadata = heatmap_tiles.groupby('col_index').first().reset_index()

        # the pulldowns corresponding to the heatmap columns
        heatmap_column_pulldowns = (
            Session.query(
                models.MassSpecHit.id.label('hit_id'),
                models.MassSpecHit.pulldown_id,
                models.CellLine.id.label('cell_line_id'),
                models.CrisprDesign.target_name
            )
            .join(models.MassSpecHit.pulldown)
            .join(models.MassSpecPulldown.cell_line)
            .join(models.CrisprDesign)
            .filter(
                models.MassSpecHit.id.in_(heatmap_column_metadata.hit_id.astype(int).tolist())
            )
            .all()
        )

        # merge the col_index with the pulldown metadata
        heatmap_column_metadata = pd.merge(
            heatmap_column_metadata[['hit_id', 'col_index']],
            pd.DataFrame(data=heatmap_column_pulldowns),
            on='hit_id'
        )

        # the protein groups corresponding to the heatmap rows
        # (the hits are included so that we can use the hit_id to merge the protein group metadata
        # with heatmap_row_metadata dataframe)
        heatmap_rows = (
            Session.query(models.MassSpecHit, models.MassSpecProteinGroup)
            .join(models.MassSpecProteinGroup.hits)
            .filter(models.MassSpecHit.id.in_(heatmap_row_metadata.hit_id.astype(int).tolist()))
            .all()
        )

        # construct the protein group metadata
        protein_group_metadata = []
        for hit, protein_group in heatmap_rows:
            metadata = payloads.generate_protein_group_payload(protein_group)
            metadata['hit_id'] = hit.id
            protein_group_metadata.append(metadata)

        # merge the row_index with the protein group metadata
        heatmap_row_metadata = pd.merge(
            heatmap_row_metadata[['hit_id', 'row_index']],
            pd.DataFrame(data=protein_group_metadata),
            on='hit_id'
        )

        # drop the now-useless hit_id column from the row and column metadata
        heatmap_row_metadata.drop(labels='hit_id', axis=1, inplace=True)
        heatmap_column_metadata.drop(labels='hit_id', axis=1, inplace=True)

        payload = {
            'metadata': {'cluster_id': cluster_id},
            'tiles': json.loads(heatmap_tiles.to_json(orient='records')),
            'rows': json.loads(heatmap_row_metadata.to_json(orient='records')),
            'columns': json.loads(heatmap_column_metadata.to_json(orient='records')),
        }
        return flask.jsonify(payload)


class MicroscopyFOV(Resource):

    def get(self, fov_id, kind, channel):
        '''
        Return the specified kind of processed data
        for a single FOV using Flask's send_file method

        kind : the kind of image data (projection, thumbnail, z-stack, etc)
        channel : one of '405', '488', or 'rgb'
        '''
        if kind != 'proj':
            flask.abort(404, 'Invalid kind')

        fov = (
            flask.current_app.Session.query(models.MicroscopyFOV)
            .filter(models.MicroscopyFOV.id == fov_id)
            .one_or_none()
        )
        if not fov:
            flask.abort(404, 'Invalid fov_id')

        processor = FOVProcessor.from_database(fov)
        processor.dst_root = flask.current_app.config.get('OPENCELL_MICROSCOPY_DIR')
        filepath_405 = processor.dst_filepath(kind='proj', channel='405', ext='tif')
        filepath_488 = processor.dst_filepath(kind='proj', channel='488', ext='tif')

        if channel == '405':
            im = tifffile.imread(filepath_405)[..., None]
            im = utils.autoscale(im, p=1)
        elif channel == '488':
            im = tifffile.imread(filepath_488)[..., None]
            im = utils.autoscale(im, p=1)
        elif channel == 'rgb':
            im = processor.make_rgb(
                tifffile.imread(filepath_405)[..., None],
                tifffile.imread(filepath_488)[..., None]
            )

        file = io.BytesIO()
        imageio.imsave(file, im, format='jpg', quality=90)
        file.seek(0)

        filename = 'FOV%04d_%s-%s.jpg' % (fov_id, kind.upper(), channel.upper())
        return flask.send_file(file, as_attachment=True, attachment_filename=filename)


class MicroscopyFOVROI(Resource):

    @cache.cached(key_prefix=cache_key)
    def get(self, roi_id, roi_kind, channel):
        '''
        Get the image data for a given ROI

        roi_kind : the kind of ROI data to return
            'proj' returns a z-projection
            'lqtile' and 'hqtile' return low- and high-quality versions of the z-stack
            (as a one-dimensional tiled array of z-slices)
        channel : one of '405' or '488'
        '''
        if roi_kind not in ['proj', 'lqtile', 'hqtile']:
            flask.abort(404, 'Invalid ROI kind %s' % roi_kind)

        roi = (
            flask.current_app.Session.query(models.MicroscopyFOVROI)
            .filter(models.MicroscopyFOVROI.id == roi_id)
            .one_or_none()
        )
        if not roi:
            flask.abort(404, 'Invalid roi_id %s' % roi_id)

        processor = FOVProcessor.from_database(roi.fov)
        relative_filepath = processor.dst_filepath(
            kind='roi',
            roi_id=roi_id,
            roi_kind=roi_kind,
            channel=channel,
            ext='jpg'
        )

        # redirect to the /data endpoint
        if flask.current_app.config.get('REDIRECT_IMAGE_REQUESTS'):
            host_url = flask.request.host_url

            # HACK: get the true request scheme from the referrer field,
            # because the host_url scheme is http even if the original request scheme was https,
            # and redirecting from https to http is blocked by CORS on firefox (but not chrome)
            if flask.request.referrer.startswith('https'):
                host_url = host_url.replace('http://', 'https://')

            return flask.redirect(f'{host_url}data/opencell-microscopy/{relative_filepath}')

        # load the file directly from the opencell-microscopy directory
        else:
            filepath = os.path.join(
                flask.current_app.config.get('OPENCELL_MICROSCOPY_DIR'), relative_filepath
            )
            if os.path.isfile(filepath):
                return flask.send_file(
                    open(filepath, 'rb'),
                    as_attachment=True,
                    attachment_filename=filepath.split(os.sep)[-1]
                )
            else:
                return flask.abort(404, 'Filepath %s does not exist' % filepath)


class CellLineAnnotation(CellLineResource):
    '''
    Get or create/update the manual annotation for a cell line
    '''
    def get(self, cell_line_id):

        line = self.get_cell_line(cell_line_id)
        if line.annotation is not None:
            return flask.jsonify({
                'comment': line.annotation.comment,
                'categories': line.annotation.categories,
                'client_metadata': line.annotation.client_metadata,
            })
        flask.abort(404)


    def put(self, cell_line_id):

        data = flask.request.get_json()
        line = self.get_cell_line(cell_line_id)
        annotation = line.annotation
        if annotation is None:
            annotation = models.CellLineAnnotation(cell_line_id=cell_line_id)

        annotation.comment = data.get('comment')
        annotation.categories = data.get('categories')
        annotation.client_metadata = data.get('client_metadata')

        try:
            db_utils.add_and_commit(
                flask.current_app.Session,
                annotation,
                errors='raise'
            )
        except Exception as error:
            flask.abort(500, str(error))

        return flask.jsonify(annotation.as_dict())


class MicroscopyFOVAnnotation(Resource):

    @staticmethod
    def get_fov(fov_id):
        return (
            flask.current_app.Session.query(models.MicroscopyFOV)
            .filter(models.MicroscopyFOV.id == fov_id)
            .one_or_none()
        )


    def get(self, fov_id):
        fov = self.get_fov(fov_id)
        if fov.annotation is not None:
            return flask.jsonify(fov.annotation.as_dict())
        flask.abort(404, 'FOV %s does not have an annotation' % fov_id)


    def put(self, fov_id):
        '''
        Create or modify the FOV annotation and, if an annotation already exists,
        delete its corresponding ROI

        Note: we delete the ROI because we assume that if it already exists,
        it will need to be recreated to reflect the changes to the annotation
        '''
        data = flask.request.get_json()
        fov = self.get_fov(fov_id)

        annotation = fov.annotation
        if annotation is None:
            annotation = models.MicroscopyFOVAnnotation(fov_id=fov_id)
        else:
            db_utils.delete_and_commit(flask.current_app.Session, fov.rois)

        annotation.categories = data.get('categories')
        annotation.client_metadata = data.get('client_metadata')
        annotation.roi_position_top = data.get('roi_position_top')
        annotation.roi_position_left = data.get('roi_position_left')

        try:
            db_utils.add_and_commit(
                flask.current_app.Session,
                annotation,
                errors='raise'
            )
        except Exception as error:
            flask.abort(500, str(error))
        return flask.jsonify(annotation.as_dict())


    def delete(self, fov_id):
        '''
        Delete both the annotation and its corresponding ROI (if one exists)

        Note: to delete the annotation's ROI, we assume that the only ROI associated with the FOV
        is the one associated with its annotation, so we can simply delete fov.rois entirely
        (this is a useful shortcut because there is currently no direct relationship
        between the annotation and its corresponding annotated ROI)
        '''
        fov = self.get_fov(fov_id)
        if fov.annotation is None:
            return flask.abort(404, 'FOV %s does not have an annotation' % fov_id)
        try:
            db_utils.delete_and_commit(flask.current_app.Session, fov.annotation)
            db_utils.delete_and_commit(flask.current_app.Session, fov.rois)
        except Exception as error:
            flask.abort(500, str(error))
        return ('', 204)


class SavedPulldownNetwork(PulldownResource):
    '''
    Cached manually-edited cytoscape layout for a cell line
    '''
    def get(self, pulldown_id):
        pulldown = self.get_pulldown(pulldown_id)
        if pulldown.network is not None:
            return flask.jsonify({
                'cytoscape_json': pulldown.network.cytoscape_json,
                'last_modified': pulldown.network.last_modified,
            })
        return flask.abort(
            404, 'Pulldown %s does not have a cached cytoscape network' % pulldown_id
        )

    def put(self, pulldown_id):
        data = flask.request.get_json()
        pulldown = self.get_pulldown(pulldown_id)
        network = pulldown.network
        if network is None:
            network = models.MassSpecPulldownNetwork(pulldown_id=pulldown_id)

        network.cytoscape_json = data.get('cytoscape_json')
        network.client_metadata = data.get('client_metadata')

        try:
            db_utils.add_and_commit(
                flask.current_app.Session,
                network,
                errors='raise'
            )
        except Exception as error:
            flask.abort(500, str(error))
        return flask.jsonify(network.as_dict())

    def delete(self, pulldown_id):
        pulldown = self.get_pulldown(pulldown_id)
        if pulldown.network is None:
            return flask.abort(
                404, 'Pulldown %s does not have a cached cytoscape network' % pulldown_id
            )
        try:
            db_utils.delete_and_commit(flask.current_app.Session, pulldown.network)
        except Exception as error:
            flask.abort(500, str(error))
        return ('', 204)


class EmbeddingPositions(Resource):

    def get(self):
        '''
        Get the positions of all cell lines in a gridded and ungridded embedding,
        along with the positions of their thumbnails in a thumbnail tile

        NOTE: for now, the names of the gridded and ungridded embeddings are hard-coded
        '''
        thumbnail_size = int(flask.request.args.get('thumbnail_size') or 100)
        thumbnail_shape = flask.request.args.get('thumbnail_shape') or 'circle'

        # generic query for embedding positions
        query = (
            flask.current_app.Session.query(
                models.CellLineEmbeddingPosition.cell_line_id,
                models.CellLineEmbeddingPosition.position_x,
                models.CellLineEmbeddingPosition.position_y,
            )
            .join(models.CellLineEmbedding)
        )

        # get the gridded embedding positions
        # hack: assume there's only one kind of embedding for a non-zero grid size
        grid_size = 40
        gridded_positions = pd.DataFrame(
            query.filter(models.CellLineEmbedding.grid_size == grid_size).all()
        )
        gridded_positions.rename(
            columns={'position_x': 'grid_x', 'position_y': 'grid_y'}, inplace=True
        )

        # get the ungridded (or 'raw') embedding positions
        # hack: hard-code the name of the embedding
        grid_size = 0
        name = (
            'december-results-full-median-vq2-target-vectors'
            '--kind=umap--n_neighbors=10--min_dist=0.1'
        )
        ungridded_positions = pd.DataFrame(
            (
                query.filter(models.CellLineEmbedding.grid_size == grid_size)
                .filter(models.CellLineEmbedding.name == name)
                .all()
            )
        )
        ungridded_positions.rename(
            columns={'position_x': 'raw_x', 'position_y': 'raw_y'}, inplace=True
        )

        # get the thumbnail tile positions
        # hack: construct the filename of the thumbnail tile manually
        tile_filename = f'tiled-cell-line-thumbnails--{thumbnail_size}px--{thumbnail_shape}.jpg'
        tile_positions = pd.DataFrame(
            flask.current_app.Session.query(
                models.ThumbnailTilePosition.cell_line_id,
                models.ThumbnailTilePosition.tile_row,
                models.ThumbnailTilePosition.tile_column
            )
            .join(models.ThumbnailTile)
            .filter(models.ThumbnailTile.filename == tile_filename)
            .all()
        )
        if not tile_positions.shape[0]:
            return flask.abort(404, "No thumbnail tile found with filename '%s'" % tile_filename)

        # get the target names and localization annotations
        targets = pd.DataFrame(
            (
                flask.current_app.Session.query(
                    models.CellLine.id.label('cell_line_id'),
                    models.CellLineAnnotation.categories,
                    models.CrisprDesign.target_name,
                )
                .join(models.CellLineAnnotation)
                .join(models.CrisprDesign)
                .all()
            )
        )
        positions = (
            tile_positions
            .merge(targets, on='cell_line_id', how='left')
            .merge(gridded_positions, on='cell_line_id', how='left')
            .merge(ungridded_positions, on='cell_line_id', how='left')
        )

        return flask.jsonify({
            'tile_filename': tile_filename,
            'positions': json.loads(positions.to_json(orient='records'))
        })


class ThumbnailTileImage(Resource):

    def get(self, filename):
        '''
        Redirect to, or load, a thumbnail tile image
        '''
        relative_filepath = os.path.join('thumbnail-tiles', filename)

        # redirect to the /data endpoint
        if flask.current_app.config.get('REDIRECT_IMAGE_REQUESTS'):
            return flask.redirect(
                f'{flask.request.host_url}data/opencell-microscopy/{relative_filepath}'
            )

        # load the file directly from the opencell-microscopy directory
        else:
            filepath = os.path.join(
                flask.current_app.config.get('OPENCELL_MICROSCOPY_DIR'), relative_filepath
            )
            return flask.send_file(
                open(filepath, 'rb'),
                as_attachment=True,
                attachment_filename=filepath.split(os.sep)[-1]
            )
