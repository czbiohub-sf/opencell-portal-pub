import argparse
import datetime
import docker
import fabric
import os
import pathlib
import time

DB_NAME = 'opencelldb'
CONTAINER_NAME = 'opencelldb-dev'


def timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def _restore_dev_db(dump_filepath):
    '''
    Create a dev database and restore it from a dump
    '''

    # resolve the path (needed if a tilde is used for the home directory)
    dump_filepath = str(pathlib.Path(dump_filepath).absolute())
    if not os.path.exists(dump_filepath):
        raise ValueError('Dump file does not exist %s' % dump_filepath)

    dump_dirpath, dump_filename = os.path.split(dump_filepath)

    # remove the existing dev database container, if it exists
    client = docker.from_env()
    container = None
    try:
        container = client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        pass

    if container is not None:
        print('Removing the existing dev database container')
        container.remove(v=True, force=True)

    print('Starting a dev database container')
    container = client.containers.run(
        image='postgres:13-alpine',
        name=CONTAINER_NAME,
        ports={5432: 5434},
        volumes=[f'{dump_dirpath}:/home/dumps:rw'],
        environment=dict(
            POSTGRES_USER='opencell', POSTGRES_PASSWORD='password', POSTGRES_DB=DB_NAME
        ),
        detach=True,
    )

    while container.status != 'running':
        print('Waiting for container to start')
        time.sleep(3)
        container = client.containers.get(CONTAINER_NAME)

    # connect the container to the existing opencell network (for convenience w pgadmin container)
    try:
        network = client.networks.get('opencell')
        network.connect(container)
    except docker.errors.NotFound:
        print('Warning: `opencell` docker network not found')

    print('Restoring database from %s' % dump_filepath)
    result = container.exec_run(
        'pg_restore --clean --create --no-privileges --no-owner --username opencell -d postgres '
        f'/home/dumps/{dump_filename}',
    )

    print(result.output.decode())
    if result.exit_code:
        print('Error calling pg_restore')
    else:
        print('Successfully restored database')


def _dump_dev_db(filename):
    '''
    Dump the dev database and write the dump to the directory containing the dumpfile
    from which the dev database was initially restored

    filename: name of the dump file (in ~/opencelldb-dumps)
    '''
    # strip the dirpath, if any, from the filename
    __, filename = os.path.split(filename)

    container = docker.from_env().containers.get(CONTAINER_NAME)
    result = container.exec_run(
        'pg_dump '
        f'--file /home/dumps/{filename} '
        '--host localhost '
        '--username opencell '
        '--verbose '
        '--format=c '
        '--blobs '
        f'{DB_NAME}'
    )

    print(result.output.decode())
    if result.exit_code:
        print('Error calling pg_dump')
    else:
        print('Database dumped to %s' % filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # remotely dump the prod database
    parser.add_argument('--dump-prod', dest='dump_prod', action='store_true', required=False)

    # copy the latest prod dump
    parser.add_argument(
        '--get-latest-prod-dump', dest='get_latest_prod_dump', action='store_true', required=False
    )

    # dump the dev database
    parser.add_argument('--dump-dev', dest='dump_dev', action='store_true', required=False)

    # restore a dev database from a dump
    parser.add_argument('--restore-dev', dest='restore_dev', action='store_true', required=False)

    # filepath to the dumpfile
    parser.add_argument('--filepath', dest='filepath', required=False)

    # ssh username and password for IBM server nodes
    parser.add_argument('--username', dest='username', required=False)
    parser.add_argument('--password', dest='password', required=False)

    args = parser.parse_args()

    # note the hard-coded IBM server node 'cap' and username
    # also note this conn object will be useless if args.password is None
    conn = fabric.Connection(
        host='cap', user=args.username, connect_kwargs={'password': args.password}
    )

    if args.dump_prod:
        conn.run('cd ~/deployed-projects/opencell/deploy/ibm-server && make dump-prod-db')

    if args.get_latest_prod_dump:
        # hard-coded path to the dumpfile directory on ESS
        remote_dump_dirpath = pathlib.Path('/gpfs/gpfsML/ML_group/KC/opencelldb-dumps')

        # local path must end in a slash
        local_dump_dirpath = '%s%s' % (args.filepath, os.sep)
        if args.filepath is None:
            raise ValueError('No dumpfile directory specified by --filepath')

        if not os.path.exists(local_dump_dirpath):
            raise ValueError('The directory %s does not exist' % local_dump_dirpath)

        # list the dumpfiles
        res = conn.run('ls %s' % remote_dump_dirpath, hide=True)
        dump_filenames = sorted(res.stdout.split('\n'))

        # download the most recent dump
        print('Downloading dumpfile %s to %s' % (dump_filenames[-1], local_dump_dirpath))
        conn.get(remote_dump_dirpath / dump_filenames[-1], local_dump_dirpath)

    if args.dump_dev:
        _dump_dev_db(filename=args.filepath)

    if args.restore_dev:
        _restore_dev_db(dump_filepath=args.filepath)
