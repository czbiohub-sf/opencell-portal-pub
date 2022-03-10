-- populate the protein_group - ensg_id association table
TRUNCATE protein_group_ensembl_association CASCADE;

WITH significant_protein_groups AS (
    SELECT protein_group_id
    FROM mass_spec_hit hit
    WHERE hit.is_significant_hit = TRUE OR hit.is_minor_hit = TRUE
    GROUP BY protein_group_id
),
protein_group_uniprot_assoc AS (
    SELECT
        id AS protein_group_id,
        split_part(unnest(uniprot_ids), '-', 1) AS uniprot_id
    FROM mass_spec_protein_group
    WHERE id IN (SELECT * FROM significant_protein_groups)
)
INSERT INTO protein_group_ensembl_association (protein_group_id, ensg_id)
SELECT protein_group_id, ensg_id
FROM
    ensembl_uniprot_association eua
    INNER JOIN protein_group_uniprot_assoc pgua ON pgua.uniprot_id = eua.uniprot_id
GROUP BY protein_group_id, ensg_id;


-- populate the protein_group - crispr_design association table
TRUNCATE protein_group_crispr_design_association;

INSERT INTO
    protein_group_crispr_design_association (protein_group_id, crispr_design_id)
SELECT
    pg.id AS protein_group_id, cd.id AS crispr_design_id
FROM
    mass_spec_protein_group pg
    INNER JOIN protein_group_ensembl_association pgea ON pgea.protein_group_id = pg.id
    INNER JOIN crispr_design cd ON cd.ensg_id = pgea.ensg_id;
