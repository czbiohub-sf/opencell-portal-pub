
import dataclasses
import os
import pathlib

from typing import List
THIS_DIR = os.path.abspath(os.path.dirname(__file__))


@dataclasses.dataclass
class Config:
    '''
    Configuration settings used by the flask app and various CLIs
    '''
    # the path to a JSON file of database credentials
    # (if not an absolute path, assumed to be relative to PROJECT_ROOT)
    DB_CREDENTIALS_FILEPATH: str

    # the path to the directory of raw microscopy data directories
    MICROSCOPY_ROOT_DIR: str

    # the path to the 'opencell-microscopy' directory of processed microscopy data
    # (usually but not necessarily a subdirectory of MICROSCOPY_ROOT_DIR)
    OPENCELL_MICROSCOPY_DIR: str = None

    # the root directory of the package is used by some database-population methods
    PROJECT_ROOT: str = str(pathlib.Path(THIS_DIR).parent.parent)

    # for flask-caching
    CACHE_TYPE: str = 'simple'
    CACHE_DEFAULT_TIMEOUT: int = 7*24*60*60

    # for redis-backed cache (unused if CACHE_TYPE is not 'redis')
    CACHE_REDIS_HOST: str = 'redis'
    CACHE_REDIS_PORT: int = 6379
    CACHE_REDIS_DB: int = 0

    # optional CORS origins (for dev/test modes)
    CORS_ORIGINS: List[str] = None

    # whether to redirect certain image-related API requests to the nginx-served /data endpoint
    REDIRECT_IMAGE_REQUESTS: bool = False

    # hack to hide non-public data and endpoints (used in the flask app)
    HIDE_PRIVATE_DATA: bool = False

    def __post_init__(self):

        # subdirectories of the microscopy data root directory
        root_dir = pathlib.Path(self.MICROSCOPY_ROOT_DIR)
        self.PLATE_MICROSCOPY_DIR = str(root_dir / 'PlateMicroscopy')
        self.PLATE_MICROSCOPY_CACHE_DIR = str(root_dir / 'opencell-microscopy' / 'cache')
        self.RAW_PIPELINE_MICROSCOPY_DIR = str(root_dir / 'raw-pipeline-microscopy')

        # directory of all processed microscopy data
        if self.OPENCELL_MICROSCOPY_DIR is None:
            self.OPENCELL_MICROSCOPY_DIR = str(root_dir / 'opencell-microscopy')

        # construct an absolute path to the db credentials
        if not os.path.isfile(self.DB_CREDENTIALS_FILEPATH):
            self.DB_CREDENTIALS_FILEPATH = os.path.join(
                self.PROJECT_ROOT, self.DB_CREDENTIALS_FILEPATH
            )

        self.CACHE_REDIS_URL = (
            f'redis://{self.CACHE_REDIS_HOST}:{self.CACHE_REDIS_PORT}/{self.CACHE_REDIS_DB}'
        )


# local dev config (backed by a local dev database)
DEV_CONFIG = Config(
    DB_CREDENTIALS_FILEPATH='db-credentials-dev.json',
    MICROSCOPY_ROOT_DIR=str(pathlib.Path.home() / 'opencell-test-data'),
    CORS_ORIGINS=['http://localhost:%s' % port for port in [8080, 8081, 9090]],
)

# local test config (backed by a local test database)
TEST_CONFIG = Config(
    DB_CREDENTIALS_FILEPATH='db-credentials-test.json',
    MICROSCOPY_ROOT_DIR=str(pathlib.Path.home() / 'opencell-test-data'),
    CORS_ORIGINS=['http://localhost:8080'],
)

# prod deployment on an IBM node (e.g. `cap`)
IBM_PROD_CONFIG = Config(
    DB_CREDENTIALS_FILEPATH='deploy/ibm-server/db-credentials-docker.json',
    MICROSCOPY_ROOT_DIR='/ML_group',
)

# config for running the app locally in dev mode but using the prod database on `cap`,
# and with the ml_group ESS partition mounted locally in '/Volumes'
REMOTE_IBM_PROD_CONFIG = Config(
    DB_CREDENTIALS_FILEPATH='deploy/ibm-server/db-credentials-external.json',
    MICROSCOPY_ROOT_DIR='/Volumes/ml_group',
    CORS_ORIGINS=['http://localhost:8080'],
)

# staging/prod config for the public app (for local staging, AWS staging, and AWS prod envs)
# HACK: MICROSCOPY_ROOT_DIR is set to /tmp because it is a required kwarg of the config class,
# but is not needed for the public app (since the public app depends only on the processed images)
# NOTE: OPENCELL_MICROSCOPY_DIR must be set to an empty string because it is unused
# but cannot be None (otherwise it will be defined in __post_init__)
STAGING_PROD_CONFIG = Config(
    DB_CREDENTIALS_FILEPATH='/run/secrets/db-credentials.json',
    MICROSCOPY_ROOT_DIR='/tmp',
    OPENCELL_MICROSCOPY_DIR='',
    REDIRECT_IMAGE_REQUESTS=True,
    HIDE_PRIVATE_DATA=True,
    CACHE_TYPE='redis',
)

LOCAL_STAGING_CONFIG = dataclasses.replace(
    STAGING_PROD_CONFIG, CACHE_REDIS_HOST='opencell-staging-redis'
)

# staging and prod on AWS
AWS_CONFIG = dataclasses.replace(
    STAGING_PROD_CONFIG, CACHE_REDIS_HOST='opencell-redis'
)


def get_config(mode):

    # fmt: off
    configs = {

        # local envs
        'dev': DEV_CONFIG,
        'test': TEST_CONFIG,
        'staging': LOCAL_STAGING_CONFIG,

        # prod env on an IBM node
        'ibm-prod': IBM_PROD_CONFIG,

        # local env with prod db credentials
        'remote-prod': REMOTE_IBM_PROD_CONFIG,

        # envs on AWS
        'aws-staging': AWS_CONFIG,
        'aws-prod': AWS_CONFIG,

        # for backwards compatibility
        # TODO: replace this with the less ambiguous 'ibm-prod'
        'prod': IBM_PROD_CONFIG,
    }
    # fmt: on

    config = configs.get(mode)
    if config is None:
        raise ValueError("Invalid app mode '%s'" % mode)

    return config
