import argparse
import logging
import pathlib
import sqlalchemy as sa
import subprocess

from opencell.database import models
from opencell.cli import utils as cli_utils

logger = logging.getLogger(__name__)


def _execute_sql(statement, interface, quiet=False):
    if not quiet:
        logger.info("Executing SQL statement: '%s'" % statement)
    with interface.engine.connect().execution_options(autocommit=True) as conn:
        result = conn.execute(sa.text(statement))
    return result


def main():

    cli_utils.configure_logging()

    parser = argparse.ArgumentParser(
        description="Basic database management commands"
    )
    parser = cli_utils.add_common_cli_args(parser)

    # drop all tables
    parser.add_argument('--drop-all', dest='drop_all', action='store_true', required=False)

    # create all tables
    parser.add_argument('--create-all', dest='create_all', action='store_true', required=False)

    # clear all tables (delete rows without deleting the tables themselves)
    parser.add_argument('--clear-all', dest='clear_all', action='store_true', required=False)

    # create indexes on important non-primary-key columns
    parser.add_argument(
        '--create-indexes', dest='create_indexes', action='store_true', required=False
    )

    # create views and materialized views
    parser.add_argument(
        '--create-views', dest='create_views', action='store_true', required=False
    )

    parser.add_argument(
        '--populate-association-tables',
        dest='populate_association_tables',
        action='store_true',
        required=False
    )

    # clear all of the microscopy- and mass-spec-related tables
    parser.add_argument('--truncate', dest='truncate', action='store_true', required=False)

    # misc cleanup (for prod)
    parser.add_argument('--cleanup', dest='cleanup', action='store_true', required=False)

    # delete non-public cell lines and all of their associated data
    parser.add_argument(
        '--delete-non-public', dest='delete_non_public', action='store_true', required=False
    )

    # delete all rows in a specific table
    parser.add_argument('--clear-table', dest='clear_table', required=False)

    # execute a sql statement
    parser.add_argument('--execute', dest='sql_statement', required=False)

    # print the number of rows in each table
    parser.add_argument('--inspect', dest='inspect', action='store_true', required=False)

    # generate schema diagram using eralchemy
    parser.add_argument(
        '--make-schema-diagram', dest='make_schema_diagram', action='store_true', required=False
    )

    args = parser.parse_args()
    interface = cli_utils.interface_from_cli_args(mode=args.mode, credentials=args.credentials)
    session = interface.make_session()

    if args.create_all:
        models.Base.metadata.create_all(interface.engine)

    if args.drop_all:
        models.Base.metadata.drop_all(interface.engine)

    if args.clear_all:
        for table in reversed(models.Base.metadata.sorted_tables):
            interface.engine.execute(table.delete())

    if args.create_indexes:
        # hard-coded list of the tables and columns on which to create indexes
        indexes = {
            'microscopy_fov': ['cell_line_id'],
            'protein_group_crispr_design_association': ['crispr_design_id', 'protein_group_id'],
            'mass_spec_hit': [
                'pulldown_id', 'protein_group_id', 'is_significant_hit', 'is_minor_hit'
            ],
        }
        for table_name, column_names in indexes.items():
            for column_name in column_names:
                _execute_sql(
                    f'''
                    create index if not exists idx_{table_name}_{column_name}
                    on {table_name}({column_name});
                    ''',
                    interface
                )

    if args.create_views:
        filepath = pathlib.Path(__file__).parent.parent / 'database' / 'define_views.sql'
        with open(filepath) as file:
            views = file.read()
        _execute_sql(views, interface, quiet=True)

    if args.populate_association_tables:
        filepath = (
            pathlib.Path(__file__).parent.parent / 'database' / 'populate_association_tables.sql'
        )
        with open(filepath) as file:
            sql = file.read()
        _execute_sql(sql, interface, quiet=True)

    if args.truncate:
        table_names = ['microscopy_dataset', 'mass_spec_pulldown', 'mass_spec_protein_group']
        for table_name in table_names:
            _execute_sql(f'truncate table {table_name} cascade;', interface)

    if args.cleanup:
        # delete pulldowns without hits
        _execute_sql(
            '''
            delete from mass_spec_pulldown pd
            where pd.id not in (select distinct(pulldown_id) from mass_spec_hit)
            ''',
            interface
        )
        # delete ROIs from FOVs without annotations (assumes that all ROIs are annotated ROIs)
        _execute_sql(
            '''
            delete from microscopy_fov_roi roi
            where roi.fov_id not in (select fov_id from microscopy_fov_annotation)
            ''',
            interface
        )
        # eliminate NaNs and Infs in the mass spec hits table
        columns = ['interaction_stoich', 'abundance_stoich']
        for column in columns:
            _execute_sql(
                f'''
                update mass_spec_hit set {column} = null
                where {column} in ('NaN', 'Infinity', '-Infinity')
                ''',
                interface
            )

    if args.delete_non_public:
        table_names = [
            'facs_dataset',
            'sequencing_dataset',
            'microscopy_fov',
            'cell_line_annotation',
            'mass_spec_pulldown',
        ]
        for table_name in table_names:
            _execute_sql(
                f'''
                delete from {table_name} where cell_line_id not in (select * from public_cell_line);
                ''',
                interface
            )

    if args.clear_table:
        table_name = args.clear_table
        interface.engine.execute(models.Base.metadata.tables[table_name].delete())

    if args.sql_statement:
        result = _execute_sql(args.sql_statement, interface)
        if result.returns_rows:
            [print(row) for row in result]

    if args.inspect:
        rows_found = False
        for table in sorted(models.Base.metadata.sorted_tables, key=lambda d: str(d)):
            num_rows = session.query(table).count()
            if num_rows > 0:
                rows_found = True
                print('%s%s' % (str(table).ljust(50, '.'), num_rows))

        if not rows_found:
            print('There are no non-empty tables in the database')


    if args.make_schema_diagram:
        subprocess.run(
            'conda activate sqlenv; eralchemy -i %s -o schema-diagram.png;' % interface.url,
            stdout=subprocess.PIPE,
            check=True,
        )


if __name__ == '__main__':
    main()
