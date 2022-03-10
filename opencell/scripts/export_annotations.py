
import argparse
import datetime
import os
import pandas as pd
import re
import sqlalchemy as sa

from opencell.database import utils


def timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dst-dir', dest='dst_dir')
    parser.add_argument('--credentials', dest='credentials', required=False)

    for dest in ['raw', 'clean', 'public_only']:
        flag = '--%s' % dest.replace('_', '-')
        parser.add_argument(flag, dest=dest, action='store_true', required=False)
        parser.set_defaults(**{dest: False})

    args = parser.parse_args()
    return args


def export_raw_annotations(engine, dst_dir):
    '''
    A CSV of all annotations (categories and comments) for all cell lines
    '''
    annotations = pd.read_sql(
        '''
        select * from cell_line_metadata
        left join cell_line_annotation
        on cell_line_metadata.cell_line_id = cell_line_annotation.cell_line_id
        order by (plate_id, well_id);
        ''',
        engine
    )

    filepath = os.path.join(dst_dir, '%s_all-raw-cell-line-annotations.csv' % timestamp())
    annotations.to_csv(filepath)


def export_clean_graded_annotations(engine, dst_dir, public_only=False):
    '''
    Export the graded annotations as CSV files in two different versions:
    one with a row for every annotation and columns for annotation_name and annotation_grade,
    and one with a row for every target and columns for each of the three grades,
    with all annotations for each target and grade concatenated into semicolon-separated strings.

    public_only : whether to filter out both unpublished cell lines and private annotations
    '''

    # hard-coded list of graded localization categories that are not published/public
    non_public_categories = [
        'small_aggregates',
        'nucleus_cytoplasm_variation',
        'textured',
        'diffuse',
        'cilia',
        'nucleolar_ring',
        'nuclear',
        'peri_golgi',
    ]

    annotations = pd.read_sql(
        '''
        select line.id as cell_line_id, cd.target_name, cd.ensg_id, ant.categories
        from cell_line line
        left join crispr_design cd on cd.id = line.crispr_design_id
        left join cell_line_annotation ant on ant.cell_line_id = line.id;
        ''',
        engine
    )

    annotations = (
        annotations.dropna(axis=0, how='any')
        .explode('categories')
        .rename(columns={'categories': 'category'})
    )

    # parse the grade from the category
    annotations['grade'] = annotations.category.apply(
        lambda s: s[-1] if not pd.isna(s) and s[-1] in ['1', '2', '3'] else 'none'
    )

    # remove the grade from the category names
    annotations['category'] = annotations.category.apply(
        lambda s: re.sub('_[1,2,3]$', '', s) if not pd.isna(s) else None
    )

    all_pr_cell_line_ids = (
        annotations.loc[annotations.category == 'publication_ready'].cell_line_id.values
    )

    public_lines_mask = annotations.cell_line_id.isin(all_pr_cell_line_ids)
    public_ants_mask = ~annotations.category.isin(non_public_categories)
    graded_mask = annotations.grade.isin(['1', '2', '3'])

    # the graded public annotations for all public targets
    annotations = annotations.loc[
        (public_lines_mask & public_ants_mask & graded_mask) if public_only else graded_mask
    ]

    annotations = annotations[['ensg_id', 'target_name', 'category', 'grade']]

    # move the annotation names into grade-specific columns
    # and concatenate them into semicolon-separated strings
    grades = {
        ('annotations_grade_%s' % grade): (
            annotations.loc[annotations.grade == grade]
            .groupby('ensg_id')
            .category
            .agg(lambda s: ';'.join(s))
        )
        for grade in ['3', '2', '1']
    }
    grades['target_name'] = annotations.groupby('ensg_id').first().target_name

    annotations_by_grade = pd.DataFrame(data=grades)
    annotations_by_grade.index.name = 'ensg_id'

    # reorder the columns and write the CSV
    column_order = [
        'ensg_id',
        'target_name',
        'annotations_grade_3',
        'annotations_grade_2',
        'annotations_grade_1'
    ]

    kind = 'public' if public_only else 'all'
    (
        annotations_by_grade.reset_index()[column_order]
        .sort_values(by='target_name')
        .to_csv(
            os.path.join(dst_dir, '%s-%s-annotations-by-grade.csv' % (timestamp(), kind)),
            index=False
        )
    )

    # finally, save the annotations as they are (one row for each annotation)
    (
        annotations
        .rename(
            columns={'category': 'annotation_name', 'grade': 'annotation_grade'}
        )
        .sort_values(
            by=['target_name', 'annotation_grade', 'annotation_name'],
            ascending=[True, False, True]
        )
        .to_csv(
            os.path.join(dst_dir, '%s-%s-annotations-flat.csv' % (timestamp(), kind)),
            index=False
        )
    )


if __name__ == '__main__':
    args = parse_args()
    url = utils.url_from_credentials(args.credentials)
    engine = sa.create_engine(url)

    if args.raw:
        export_raw_annotations(engine, args.dst_dir)
        print('Raw annotations exported to %s' % args.dst_dir)

    if args.clean:
        export_clean_graded_annotations(engine, args.dst_dir, public_only=args.public_only)
        print('Clean annotations exported to %s' % args.dst_dir)
