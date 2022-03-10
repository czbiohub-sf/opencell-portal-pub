import logging

from opencell.database import utils
from opencell.api import settings


def add_common_cli_args(parser):
    '''
    Define common database-related CLI arguments for argparse-based CLIs
    '''
    # deployment mode (dev, test, prod, etc)
    parser.add_argument(
        '--mode',
        dest='mode',
        required=True,
        choices=('dev', 'test', 'staging', 'prod', 'remote-prod')
    )
    # path to a JSON file with database credentials
    # (optional; overrides the filepath defined in opencell.api.settings)
    parser.add_argument('--credentials', dest='credentials', required=False)
    return parser


def interface_from_cli_args(mode, credentials=None):
    '''
    Initialize a SQLAlchemyInterface from parsed CLI args
    '''
    config = settings.get_config(mode)
    url = utils.url_from_credentials(credentials or config.DB_CREDENTIALS_FILEPATH)
    interface = utils.SQLAlchemyInterface.from_url(url)
    return interface


def configure_logging(log_filepath=None):
    '''
    Configure logging for CLIs
    '''
    # configure the root logger, not the 'opencell' logger,
    # since we want to configure the loggers in both modules and scripts
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)s in %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    if log_filepath is not None:
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
