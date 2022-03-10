import argparse
import logging
import os

from opencell.api import settings
from opencell.cli import utils as cli_utils
from opencell.database import fov_operations, metadata_operations, file_utils
from opencell.imaging.managers import PlateMicroscopyManager

logger = logging.getLogger(__name__)


def construct_plate_microscopy_metadata(plate_microscopy_manager):
    '''
    '''
    logger.info('Caching os.walk results')
    if not hasattr(plate_microscopy_manager, 'os_walk'):
        plate_microscopy_manager.cache_os_walk()

    logger.info('Constructing metadata')
    plate_microscopy_manager.construct_metadata()

    logger.info('Constructing raw metadata')
    plate_microscopy_manager.construct_raw_metadata()

    logger.info('Caching metadata')
    plate_microscopy_manager.cache_metadata(overwrite=True)


def inspect_plate_microscopy_metadata(plate_microscopy_manager):
    '''
    '''
    print(
        f'''
        All metadata rows:          {plate_microscopy_manager.md.shape[0]}
        metadata.is_raw.sum():      {plate_microscopy_manager.md.is_raw.sum()}
        Parsed raw metadata rows:   {plate_microscopy_manager.md_raw.shape[0]}
        '''
    )


def insert_plate_microscopy_fovs(session, cache_dir=None):
    '''
    Insert all raw FOVs from the PlateMicroscopy directory

    To speed things up, we group the FOVs by (plate_id, well_id)
    so that all FOVs for each cell_line are inserted together

    cache_dir : local directory in which the results of calling os.walk
        on the PlateMicroscopy directory are cached
    '''
    # PlateMicroscopy FOVs are all from the original sorted lines
    # (and never from resorted lines)
    sort_count = 1

    pm = PlateMicroscopyManager(cache_dir=cache_dir)

    # generate the raw metadata
    pm.construct_metadata()
    pm.construct_raw_metadata()
    metadata = pm.md_raw.groupby(['plate_id', 'well_id'])

    plate_id = None
    for group in metadata.groups:
        if plate_id is None or group[0] != plate_id:
            logger.info('Inserting PlateMicroscopy FOVs for %s' % group[0])
        plate_id, well_id = group
        group_metadata = metadata.get_group(group)

        line_ops = metadata_operations.PolyclonalLineOperations.from_plate_well(
            session, plate_id, well_id, sort_count=sort_count
        )
        if not line_ops:
            logger.warning(
                'Cannot insert PlateMicroscopy FOVs for (%s, %s) because no cell line exists'
                % group
            )
            continue
        line_ops.insert_microscopy_fovs(session, group_metadata)


def main():

    parser = argparse.ArgumentParser(description='PlateMicroscopy-related methods')
    parser = cli_utils.add_common_cli_args(parser)
    cli_utils.configure_logging()

    actions = [
        'inspect_metadata',
        'construct_metadata',
        'insert_datasets',
        'insert_fovs',
    ]
    for action in actions:
        flag = '--%s' % action.replace('_', '-')
        parser.add_argument(flag, dest=action, action='store_true', required=False)
        parser.set_defaults(**{action: False})

    args = parser.parse_args()
    config = settings.get_config(args.mode)
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)
    session = interface.make_session()

    # construct the PlateMicroscopy metadata
    # (this is a dataframe of FOV metadata with one row per FOV)
    if args.construct_metadata:
        manager = PlateMicroscopyManager(
            config.PLATE_MICROSCOPY_DIR, config.PLATE_MICROSCOPY_CACHE_DIR
        )
        construct_plate_microscopy_metadata(manager)

    # inspect the cached PlateMicroscopy metadata
    if args.inspect_metadata:
        manager = PlateMicroscopyManager(
            config.PLATE_MICROSCOPY_DIR, config.PLATE_MICROSCOPY_CACHE_DIR
        )
        inspect_plate_microscopy_metadata(manager)

    # insert the 'legacy' pipeline microscopy datasets in the 'PlateMicroscopy' directory
    # (these are datasets up to PML0179)
    if args.insert_datasets:
        filepath = os.path.join(
            config.PROJECT_ROOT,
            'opencell',
            'tests',
            'artifacts',
            'data',
            'metadata',
            '2019-12-05_Pipeline-microscopy-master-key_PlateMicroscopy-MLs-raw.csv'
        )
        plate_microscopy_metadata = file_utils.load_legacy_microscopy_master_key(filepath)
        for _, metadata_row in plate_microscopy_metadata.iterrows():
            fov_operations.insert_microscopy_dataset(
                session, metadata_row, root_directory='plate_microscopy', update=False
            )

    # insert all FOVs from the 'PlateMicroscopy' directory
    # (should only be called once, when initially populating a new database,
    # because the 'PlateMicroscopy' directory is static)
    if args.insert_fovs:
        insert_plate_microscopy_fovs(session, cache_dir=config.PLATE_MICROSCOPY_CACHE_DIR)


if __name__ == '__main__':
    main()
