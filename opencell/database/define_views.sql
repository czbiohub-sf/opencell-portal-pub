CREATE OR REPLACE VIEW cell_line_metadata AS (
    SELECT
        cd.plate_design_id AS plate_id,
        cd.well_id,
        cd.target_name,
        cell_line.id AS cell_line_id
    FROM
        crispr_design cd
        JOIN cell_line ON cell_line.crispr_design_id = cd.id
    ORDER BY ROW(cd.plate_design_id, cd.well_id)
);


CREATE OR REPLACE VIEW public_cell_line AS (
    SELECT
        ant.cell_line_id AS id
    FROM
        (
            SELECT
                ant_1.cell_line_id,
                unnest(
                    ARRAY(
                        SELECT json_array_elements_text(ant_1.categories :: json) AS json_array_elements_text
                    )
                ) AS category
            FROM
                cell_line_annotation ant_1
                LEFT JOIN cell_line ON cell_line.id = ant_1.cell_line_id
        ) ant
    WHERE
        ant.category = 'publication_ready'
);


CREATE OR REPLACE VIEW fov_rank AS (
    SELECT
        fov.cell_line_id,
        fov.id AS fov_id,
        (result.data ->> 'score') :: double precision AS score,
        row_number() OVER (
            PARTITION BY fov.cell_line_id
            ORDER BY
                COALESCE((result.data ->> 'score') :: double precision, -1) DESC
        ) AS rank
    FROM
        microscopy_fov fov
        LEFT JOIN microscopy_fov_result result ON fov.id = result.fov_id
    WHERE
        result.kind = 'fov-features'
);


DROP MATERIALIZED VIEW IF EXISTS searchable_hgnc_metadata;

CREATE MATERIALIZED VIEW searchable_hgnc_metadata AS (
    WITH published_cell_line AS (
        SELECT
            ant.cell_line_id AS id,
            cd.ensg_id
        FROM
            (
                SELECT
                    cell_line_annotation.cell_line_id,
                    json_array_elements_text(cell_line_annotation.categories :: json) AS category
                FROM
                    cell_line_annotation
            ) ant
            JOIN cell_line ON cell_line.id = ant.cell_line_id
            JOIN crispr_design cd ON cd.id = cell_line.crispr_design_id
        WHERE
            ant.category = 'publication_ready'
    ),
    abundance_by_ensg_id AS (
        SELECT
            ensg_id,
            max(ab.measured_transcript_expression) AS measured_expression,
            max(ab.measured_protein_concentration) AS measured_abundance,
            max(ab.imputed_protein_concentration) AS imputed_abundance
        FROM
            ensembl_uniprot_association eua
            INNER JOIN abundance_measurement ab ON ab.uniprot_id = eua.uniprot_id
        GROUP BY
            ensg_id
    )
    SELECT
        hgnc.ensg_id,
        hgnc.symbol AS gene_name,
        hgnc.name AS protein_name,
        published_cell_line.id AS published_cell_line_id,
        pgea.protein_group_id AS significant_protein_group_id,
        ab.measured_expression,
        ab.measured_abundance,
        ab.imputed_abundance,
        to_tsvector(concat_ws(' ', name, prev_name, alias_name)) AS content
    FROM
        hgnc_metadata hgnc
        LEFT JOIN published_cell_line ON hgnc.ensg_id = published_cell_line.ensg_id
        LEFT JOIN protein_group_ensembl_association pgea ON pgea.ensg_id = hgnc.ensg_id
        LEFT JOIN abundance_by_ensg_id ab ON ab.ensg_id = hgnc.ensg_id
);
