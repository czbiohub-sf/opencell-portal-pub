import datetime
import json
import logging
import pandas as pd
import re
import sqlalchemy as sa

from contextlib import contextmanager

logger = logging.getLogger(__name__)


def timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def url_from_credentials(credentials_filepath):
    '''
    Generate database URL from credentials in a JSON file
    '''
    with open(credentials_filepath) as file:
        credentials = json.load(file)
    url = '{driver}://{username}:{password}@{host}:{port}/{dbname}'
    return url.format(**credentials)


class SQLAlchemyInterface:
    def __init__(self, url):
        self.url = url
        self.engine = sa.create_engine(url)
        self._session_maker = sa.orm.sessionmaker(bind=self.engine)

    def make_session(self):
        return self._session_maker()

    def make_scoped_session(self):
        return sa.orm.scoped_session(self._session_maker)

    @classmethod
    def from_url(cls, url):
        return cls(url)


@contextmanager
def session_scope(sqlalchemy_interface):
    session = sqlalchemy_interface.make_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_and_commit(session, instances, errors='warn'):
    if not isinstance(instances, list):
        instances = [instances]
    try:
        session.add_all(instances)
        session.commit()
    except Exception as exception:
        session.rollback()
        if errors == 'raise':
            raise
        if errors == 'warn':
            logger.warning('Error in add_and_commit: %s' % exception)


def delete_and_commit(session, instances, errors='warn'):
    if not isinstance(instances, list):
        instances = [instances]

    for instance in instances:
        try:
            session.delete(instance)
            session.commit()
        except Exception as exception:
            session.rollback()
            if errors == 'raise':
                raise
            if errors == 'warn':
                logger.warning('Error in delete_and_commit: %s' % exception)


def to_jsonable(data):
    '''
    hackish way to make a dict JSON-safe
    '''
    return json.loads(pd.Series(data=data).to_json())


def format_well_id(well_id):
    '''
    Zero-pad well_ids like 'A1' to 'A01'
    '''
    if re.match(r'^[A-H][1-9]$', well_id):
        row, column = well_id
        well_id = '%s0%s' % (row, column)
    return well_id


def format_plate_design_id(design_id):
    '''
    Format a plate design id if it's not already in the format required by the database
    This format is: `'P%04d' % plate_number`

    For convenience, this method is relatively permissive.

    All of the following examples will yield 'P0001':
    'Plate 1, 'plate1', 'plate01', '01', 1
    '''

    design_id = str(design_id)
    result = re.match(r'^P[0-9]{4}$', design_id)
    if result is None:
        plate_number = None

        # the design_id either begins with 'plate' or is the plate_number itself
        result = re.match(r'^p?(?:late)? ?([0-9]+)$', design_id.lower())
        if result:
            plate_number = result.groups()[0]
        else:
            plate_number = design_id

        try:
            plate_number = int(plate_number)
        except ValueError:
            raise ValueError("'%s' is not a valid design_id" % design_id)

        design_id = ('P%04d' % plate_number)
    return design_id


def is_sequence(sequence):
    alphabet = set(['a', 't', 'g', 'c'])
    return set(sequence.lower()).issubset(alphabet)


def current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d')
