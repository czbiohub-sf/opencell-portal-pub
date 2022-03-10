import os
from pathlib import Path
import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from opencell.database import models, utils


@pytest.fixture(scope='session')
def db_credentials():
    return utils.url_from_credentials('db-credentials-test.json')


@pytest.fixture(scope='session')
def engine(db_credentials):
    # use echo=True to monitor emitted SQL
    engine = sa.create_engine(db_credentials, echo=False)
    models.Base.metadata.create_all(engine)
    yield engine
    models.Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session(engine):
    '''
    Set up and tear down a database connection
    and an ordinary, automatically-managed sqlalchemy session
    (i.e., one unenclosed by an outer transaction)
    '''
    connection = engine.connect()
    session = sa.orm.sessionmaker()(bind=connection)
    yield session
    session.close()
    connection.close()

    # clear all of the tables to 'reset' the test database
    for table in reversed(models.Base.metadata.sorted_tables):
        engine.execute(table.delete())


class SessionManager:
    '''
    This class provides an alternative way to create a `session` instance
    for a pytest fixture that encloses the session in a non-ORM transaction
    that can be rolled back during cleanup.

    This avoids the need to manually clean up the database after the test,
    but leads to the non-intuitive behavior that calling session.rollback()
    within a test function rolls back everything the test function has committed

    This approach is taken from the sqlalchemy docs:
    https://docs.sqlalchemy.org/en/14/orm/session_transaction.html
    #joining-a-session-into-an-external-transaction-such-as-for-test-suites

    For reference, a `session` fixture that uses this class would look like this:
        sm = SessionManager(engine)
        yield sm.session
        sm.clean_up()
    '''
    def __init__(self, engine):
        self.connection = engine.connect()
        self.session = sa.orm.sessionmaker()(bind=self.connection)

        # begin a non-ORM transaction to which self.session is automatically assigned
        self.transaction = self.connection.begin()

        # begin a non-ORM savepoint (to which self.session is also automatically assigned)
        # (this allows a test function to call session.rollback
        # without rolling back the transaction itself)
        self.nested = self.connection.begin_nested()

        # use an event listener to start a new savepoint whenever the open savepoint is closed,
        # which happens whenever session.rollback() is called by the test function.
        # note that the 'after_transaction_end' event is triggered not only by session.rollback()
        # but also twice by calls to session.commit (once for the automatic call to session.flush,
        # and once by commit itself).
        # however, only a call to session.rollback will switch self.nested.is_active to False
        # (in other words, session.commit() does not exit the savepoint).
        # this means that if a test function calls session.rollback,
        # *everything* the test function has already committed will be rolled back
        @sa.event.listens_for(self.session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if not self.nested.is_active:
                self.nested = self.connection.begin_nested()

    def clean_up(self):
        self.session.close()
        # transaction.rollback roll backs *all* of the changes
        # that the test function made, even if it called session.commit
        self.transaction.rollback()
        self.connection.close()
