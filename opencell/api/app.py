import argparse
import os

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from opencell.api import resources
from opencell.api import settings
from opencell.database import models, utils
from opencell.api.cache import cache


def create_session_registry(url):
    '''
    Create a sqlalchemy scoped session registry

    The 'registry' is the `Session` object below.
    Note that, although this object is a 'registry' that manages session instances,
    it also proxies session-bound methods (like query), so that the registry
    itself can be treated like a session instance, enabling lines like
    `Session.query(models.SomeModel)`
    '''
    engine = create_engine(url)
    session_maker = sessionmaker(bind=engine)
    Session = scoped_session(session_maker)
    return Session


def create_app(config=None):

    if not config:
        config = settings.get_config(os.environ.get('MODE'))

    app = Flask(__name__)
    app.config.from_object(config)
    if app.config.get('CORS_ORIGINS'):
        CORS(app, origins=app.config['CORS_ORIGINS'])

    cache.init_app(app)
    api = Api()

    # search by exact gene name for cell line ids and ENSG ids
    # used only in handleGeneNameSearch to switch to the target page or interactor page
    api.add_resource(resources.GeneNameSearch, '/search/<string:gene_name>')

    # full-text search
    # used only to populate the table of search results on the SearchResults page
    api.add_resource(resources.FullTextSearch, '/fsearch/<string:query>')

    # annotations (or 'comments') from uniprotkb
    api.add_resource(resources.UniProtKBAnnotation, '/uniprotkb_annotation/<string:uniprot_id>')

    # the full abundance dataset
    api.add_resource(resources.AbundanceDataset, '/abundance')

    # a list of all opencell target names and their uniprot protein names
    # used to populate the suggestions in the gene-name search component in the navbar
    api.add_resource(resources.TargetNames, '/target_names')

    # the metadata for all cell lines
    api.add_resource(resources.CellLines, '/lines')

    # the metadata for the specified cell line
    api.add_resource(resources.CellLine, '/lines/<int:cell_line_id>')

    # the FACS histograms for a cell line (used only for the private app)
    api.add_resource(resources.FACSDataset, '/lines/<int:cell_line_id>/facs')

    # the metadata for all FOVs for a cell line
    api.add_resource(resources.MicroscopyFOVMetadata, '/lines/<int:cell_line_id>/fovs')

    # the metadata for all hits of a pulldown
    # used by the massSpecScatterPlot component
    api.add_resource(resources.PulldownHits, '/pulldowns/<int:pulldown_id>/hits')

    # the interaction network for a pulldown (in cytoscape schema)
    # used by the cytoscape component and the massSpecTable component
    api.add_resource(
        resources.PulldownNetwork, '/pulldowns/<int:pulldown_id>/network'
    )

    # the saved network for a pulldown (including human-edited layout coordinates)
    # NOTE: currently unused
    api.add_resource(
        resources.SavedPulldownNetwork, '/pulldowns/<int:pulldown_id>/saved_network'
    )

    # the metadata for an ensg_id (used by the InteractorProfile)
    api.add_resource(resources.InteractorMetadata, '/interactors/<string:ensg_id>')

    # the cytoscape network for an interactor (identified by ensg_id)
    api.add_resource(resources.InteractorNetwork, '/interactors/<string:ensg_id>/network')

    # FOV image data (used only to get the FOV z-projections on the /fovs page)
    api.add_resource(
        resources.MicroscopyFOV, '/fovs/<int:fov_id>/<string:kind>/<string:channel>'
    )

    # ROI image data (for z-projections and z-stacks)
    api.add_resource(
        resources.MicroscopyFOVROI, '/rois/<int:roi_id>/<string:roi_kind>/<string:channel>'
    )

    # hack to 'disable' non-public endpoints on AWS
    if not config.HIDE_PRIVATE_DATA:

        # convenience endpoint to clear the cache
        api.add_resource(resources.ClearCache, '/clear_cache')

        # unused endpoint (was for the mass spec heatmap)
        api.add_resource(resources.PulldownClusters, '/pulldowns/<int:pulldown_id>/clusters')

        # cell line and FOV annotations
        api.add_resource(resources.CellLineAnnotation, '/lines/<int:cell_line_id>/annotation')
        api.add_resource(resources.MicroscopyFOVAnnotation, '/fovs/<int:fov_id>/annotation')

        # endpoints for the UMAP page
        api.add_resource(resources.EmbeddingPositions, '/embedding_positions')
        api.add_resource(resources.ThumbnailTileImage, '/thumbnail_tiles/<string:filename>')

    api.init_app(app)

    # create an instance of sqlalchemy's scoped_session registry
    url = utils.url_from_credentials(app.config['DB_CREDENTIALS_FILEPATH'])
    app.Session = create_session_registry(url)

    # close the session instance when a request is completed
    @app.teardown_appcontext
    def remove_session(error=None):
        app.Session.remove()

    return app


def parse_args():
    '''
    CLI args for running the app via app.run (i.e., in non-production environments)
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', dest='mode', required=True)
    parser.add_argument('--credentials', dest='credentials_filepath')
    parser.add_argument('--opencell-microscopy-dir', dest='opencell_microscopy_dir')
    return parser.parse_args()


def main():
    args = parse_args()
    config = settings.get_config(args.mode)

    if args.credentials_filepath:
        config.DB_CREDENTIALS_FILEPATH = args.credentials_filepath

    if args.opencell_microscopy_dir:
        config.OPENCELL_MICROSCOPY_DIR = args.opencell_microscopy_dir

    app = create_app(config)
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
