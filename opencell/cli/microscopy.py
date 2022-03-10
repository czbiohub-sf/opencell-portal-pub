import argparse
import dask
import dask.diagnostics
import logging
import os
import pathlib
import sqlalchemy as sa

from opencell.api import settings
from opencell.cli import utils as cli_utils
from opencell.database import models, fov_operations, file_utils, utils as db_utils
from opencell.database.fov_operations import MicroscopyFOVOperations
from opencell.imaging.processors import FOVProcessor

logger = logging.getLogger(__name__)

try:
    import dragonfly_automation.fov_models.fov_models
except ModuleNotFoundError:
    logger.warning(
        'The dragonfly_automation package was not found, so calculating FOV features will not work'
    )


class FOVTaskDefinition:

    def __init__(self, processor_method, populator_method):
        '''
        An FOV task is a combination of a processor method of the FOVProcessor class
        and a database-population method of the MicroscopyFOVOperations class
        '''
        if not hasattr(FOVProcessor, processor_method):
            raise ValueError("'%s' is not a valid processor method")

        if populator_method is not None and not hasattr(MicroscopyFOVOperations, populator_method):
            raise ValueError("'%s' is not a valid populator method")

        self.processor_method = processor_method
        self.populator_method = populator_method

    def get_processor_method(self, fov_processor):
        return getattr(fov_processor, self.processor_method)

    def get_populator_method(self, fov_operations):
        if self.populator_method is None:
            return None
        return getattr(fov_operations, self.populator_method)


TASK_DEFINITIONS = [
    FOVTaskDefinition(
        processor_method='process_raw_tiff', populator_method='insert_raw_tiff_metadata'
    ),
    FOVTaskDefinition(
        processor_method='calculate_fov_features', populator_method='insert_fov_features'
    ),
    FOVTaskDefinition(
        processor_method='generate_fov_thumbnails', populator_method='insert_fov_thumbnails'
    ),
    FOVTaskDefinition(
        processor_method='calculate_z_profiles', populator_method='insert_z_profiles'
    ),
    FOVTaskDefinition(
        processor_method='generate_clean_tiff',
        populator_method='insert_clean_tiff_metadata'
    ),
    FOVTaskDefinition(
        processor_method='crop_corner_rois', populator_method='insert_corner_rois'
    ),
    FOVTaskDefinition(
        processor_method='crop_annotated_roi', populator_method='insert_annotated_roi'
    ),
    FOVTaskDefinition(
        processor_method='generate_annotated_roi_thumbnails',
        populator_method='insert_roi_thumbnails'
    ),
    FOVTaskDefinition(
        processor_method='generate_nucleus_segmentation', populator_method=None
    )
]


def parse_args():
    parser = argparse.ArgumentParser()

    # deployment mode - one of 'dev', 'test', 'staging', 'prod'
    parser.add_argument('--mode', dest='mode', required=True)

    # path to JSON file with database credentials
    # (if provided, overrides the filepath defined in opencell.api.settings)
    parser.add_argument('--credentials', dest='credentials', required=False)

    # the filepath to a snapshot of the pipeline-microscopy-master-key google sheet
    # (only used with --insert-datasets)
    parser.add_argument('--snapshot-filepath', dest='snapshot_filepath')

    # the pml_id whose FOVs are to be inserted or processed
    parser.add_argument('--pml-id', dest='pml_id')

    # FOV thumbnail scale and quality
    parser.add_argument('--thumbnail-scale', dest='thumbnail_scale', required=False)
    parser.add_argument('--thumbnail-quality', dest='thumbnail_quality', required=False)

    # CLI args whose presence in the command sets them to True
    action_arg_dests = [

        # insert raw-pipeline-microscopy datasets
        'insert_datasets',

        # insert raw-pipeline-microscopy fovs
        'insert_fovs',

        # whether to overwrite existing datasets
        'force_update',

        # whether to process all FOVs or only unprocessed FOVs
        'process_all',
    ]

    # all task names are also action args
    action_arg_dests.extend([task_def.processor_method for task_def in TASK_DEFINITIONS])

    for dest in action_arg_dests:
        flag = '--%s' % dest.replace('_', '-')
        parser.add_argument(flag, dest=dest, action='store_true', required=False)
        parser.set_defaults(**{dest: False})

    args = parser.parse_args()
    return args


class FOVTaskManager:

    def __init__(self, fov, config, task_name):

        task_names = [task_def.processor_method for task_def in TASK_DEFINITIONS]
        if task_name not in task_names:
            raise ValueError("Invalid task name '%s'" % task_name)

        self.task_definition = TASK_DEFINITIONS[task_names.index(task_name)]

        # instantiate a processor and operations class for each FOV
        self.fov_processor = FOVProcessor.from_database(fov)
        self.fov_operations = MicroscopyFOVOperations(fov.id, errors='raise')

        self.fov_processor.set_paths(
            plate_microscopy_dir=config.PLATE_MICROSCOPY_DIR,
            raw_pipeline_microscopy_dir=config.RAW_PIPELINE_MICROSCOPY_DIR,
            dst_root_dir=config.OPENCELL_MICROSCOPY_DIR
        )

    def do_task(self, Session, **task_kwargs):
        '''
        '''
        error_occurred = False
        processor_method = self.task_definition.get_processor_method(self.fov_processor)
        populator_method = self.task_definition.get_populator_method(self.fov_operations)
        try:
            result = processor_method(**task_kwargs)
            if populator_method is not None:
                populator_method(Session(), result)
        except Exception as error:
            error_occurred = True
            logger.error(
                "Error running task '%s' on fov_id %s: %s"
                % (self.task_definition.processor_method, self.fov_processor.fov_id, str(error))
            )
        return error_occurred


def do_fov_tasks(Session, config, task_name, fovs=None, **task_kwargs):
    '''
    Run a 'task' (a method of the FOVProcessor class) on all, or a subset of, the raw FOVs

    Parameters
    ----------
    Session :
    config : an API config (defined in opencell.api.settings)
    task_name : the name of the task (must be present in TASK_DEFINITIONS)
    task_kwargs : the kwargs required for the task (if any)
    fovs : optional list of FOVs to be processed (if None, all FOVs are processed)
    '''

    # if a list of FOVs was not provided, process all FOVs
    if fovs is None:
        fovs = Session.query(models.MicroscopyFOV).all()

    if not len(fovs):
        logger.warning('There are no FOVs to be processed')
        return

    tasks = []
    for fov in fovs:
        task_manager = FOVTaskManager(fov, config=config, task_name=task_name)
        task = dask.delayed(task_manager.do_task)(Session, **task_kwargs)
        tasks.append(task)

    logger.info("Performing task '%s' on %s FOVs" % (task_name, len(fovs)))
    with dask.diagnostics.ProgressBar():
        error_flags = dask.compute(*tasks)

    if sum(error_flags):
        logger.info(
            "Errors occurred for %s/%s FOVs while running task '%s'"
            % (sum(error_flags), len(fovs), task_name)
        )
    else:
        logger.info("No errors occurred while running task '%s'" % task_name)


def main():

    args = parse_args()
    config = settings.get_config(args.mode)
    interface = cli_utils.interface_from_cli_args(args.mode, args.credentials)

    log_dir = os.path.join(config.OPENCELL_MICROSCOPY_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, '%s_microscopy-cli.log' % db_utils.timestamp())
    cli_utils.configure_logging(log_filepath)

    # note: a scoped session is required for dask-delayed processing methods
    Session = interface.make_scoped_session()

    # insert microscopy datasets in the 'raw-pipeline-microscopy' directory
    # (these datasets started at PML0196, are manually defined in the 'PMLs' tab
    # of the 'pipeline-microscopy-master-key' google sheet,
    # and are always acquired using the dragonfly-automation script)
    if args.insert_datasets:
        root_directory = 'raw_pipeline_microscopy'
        snapshot = file_utils.load_pipeline_microscopy_master_key(args.snapshot_filepath)
        for _, row in snapshot.iterrows():
            fov_operations.insert_microscopy_dataset(
                Session, row, root_directory, update=args.force_update
            )

    # insert the FOVs from a dataset in the 'raw-pipeline-microscopy' directory
    # (this is called to update the database with the FOVs from new PML datasets)
    if args.insert_fovs:
        filepath = os.path.join(config.RAW_PIPELINE_MICROSCOPY_DIR, args.pml_id, 'fov-metadata.csv')
        fov_metadata = file_utils.load_pipeline_microscopy_dataset_metadata(filepath)
        logger.info('Inserting %s FOVs from %s' % (fov_metadata.shape[0], args.pml_id))
        fov_operations.insert_microscopy_fovs(Session, fov_metadata)

    # if a pml_id was provided, only process the FOVs from that dataset
    fovs = None
    if args.pml_id:
        dataset = (
            Session.query(models.MicroscopyDataset)
            .filter(models.MicroscopyDataset.pml_id == args.pml_id)
            .one_or_none()
        )
        if dataset is None:
            raise ValueError('No dataset found for %s' % args.pml_id)
        fovs = dataset.fovs

    # process all raw tiffs
    if args.process_raw_tiff:
        task_name = 'process_raw_tiff'
        if not args.process_all:
            fovs = fov_operations.get_unprocessed_fovs(Session, result_kind='raw-tiff-metadata')
        do_fov_tasks(Session, config, task_name, fovs=fovs)

    # calculate z-profiles
    if args.calculate_z_profiles:
        task_name = 'calculate_z_profiles'
        if not args.process_all:
            fovs = fov_operations.get_unprocessed_fovs(Session, result_kind='z-profiles')
        do_fov_tasks(Session, config, task_name, fovs=fovs)

    # crop around the cell layer in z
    if args.generate_clean_tiff:
        task_name = 'generate_clean_tiff'
        if not args.process_all:
            fovs = fov_operations.get_unprocessed_fovs(Session, result_kind='clean-tiff-metadata')
        do_fov_tasks(Session, config, task_name, fovs=fovs)

    # calculate FOV features and score (requires the dragonfly-automation package)
    if args.calculate_fov_features:
        task_name = 'calculate_fov_features'

        # load and train the FOV scorer from the dragonfly-automation package
        dragonfly_automation_dirpath = pathlib.Path(dragonfly_automation.__file__).parent
        model_dir = dragonfly_automation_dirpath / 'fov_models' / 'training_data' / '2019-10-08'
        fov_scorer = dragonfly_automation.fov_models.fov_models.PipelineFOVScorer(
            model_dir=str(model_dir),
            model_type='regression',
            mode='training',
            random_state=42
        )
        fov_scorer.load()
        fov_scorer.train()

        if not args.process_all:
            fovs = fov_operations.get_unprocessed_fovs(Session, result_kind='fov-features')
        do_fov_tasks(Session, config, task_name, fovs=fovs, fov_scorer=fov_scorer)

    if args.generate_fov_thumbnails:
        task_name = 'generate_fov_thumbnails'
        do_fov_tasks(
            Session,
            config,
            task_name,
            fovs=fovs,
            scale=int(args.thumbnail_scale),
            quality=int(args.thumbnail_quality)
        )

    if args.crop_corner_rois:
        task_name = 'crop_corner_rois'

        # only crop ROIs from the two highest-scoring FOVs per line
        query = (
            Session.query(models.CellLine)
            .options(
                sa.orm.joinedload(models.CellLine.fovs, innerjoin=True)
                .joinedload(models.MicroscopyFOV.results, innerjoin=True)
            )
        )
        fovs_to_crop = []
        for line in query.all():
            fovs_to_crop.extend(line.get_top_scoring_fovs(ntop=2))
        do_fov_tasks(Session, config, task_name, fovs=fovs_to_crop)

    if args.crop_annotated_roi:
        task_name = 'crop_annotated_roi'
        query = (
            Session.query(models.MicroscopyFOV)
            .filter(models.MicroscopyFOV.annotation.has())
        )
        # only process newly-annotated FOVs
        # (this means ROIs from FOVs with existing but newly-edited annotations will not be updated)
        if not args.process_all:
            query = query.filter(~models.MicroscopyFOV.rois.any())
        do_fov_tasks(Session, config, task_name, fovs=query.all())

    if args.generate_annotated_roi_thumbnails:
        task_name = 'generate_annotated_roi_thumbnails'
        query = (
            Session.query(models.MicroscopyFOV).join(models.MicroscopyFOVROI)
            .filter(models.MicroscopyFOV.annotation.has())
        )
        # only process newly-cropped ROIs (those that don't already have thumbnails)
        if not args.process_all:
            query = query.filter(~models.MicroscopyFOVROI.thumbnails.any())
        do_fov_tasks(
            Session,
            config,
            task_name,
            fovs=query.all(),
            scale=int(args.thumbnail_scale),
            quality=int(args.thumbnail_quality)
        )

    if args.generate_nucleus_segmentation:
        task_name = 'generate_nucleus_segmentation'
        fovs = Session.query(models.MicroscopyFOV).all()
        do_fov_tasks(Session, config, task_name, fovs=fovs)


if __name__ == '__main__':
    main()
