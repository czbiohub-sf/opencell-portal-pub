
export const localizationCategories = [

    // public annotations
    {'name': 'membrane', 'num': 191, status: 'public'},
    {'name': 'vesicles', 'num': 394, status: 'public'},
    {'name': 'er', 'num': 162, status: 'public'},
    {'name': 'golgi', 'num': 112, status: 'public'},
    {'name': 'mitochondria', 'num': 16, status: 'public'},
    {'name': 'centrosome', 'num': 69, status: 'public'},
    {'name': 'cytoskeleton', 'num': 60, status: 'public'},
    {'name': 'chromatin', 'num': 145, status: 'public'},
    {'name': 'nucleoplasm', 'num': 674, status: 'public'},
    {'name': 'nuclear_membrane', 'num': 48, status: 'public'},
    {'name': 'nucleolus_gc', 'num': 100, status: 'public'},
    {'name': 'nucleolus_fc_dfc', 'num': 37, status: 'public'},
    {'name': 'nuclear_punctae', 'num': 152, status: 'public'},
    {'name': 'big_aggregates', 'num': 73, status: 'public'},
    {'name': 'cell_contact', 'num': 59, status: 'public'},
    {'name': 'focal_adhesions', 'num': 13, status: 'public'},
    {'name': 'cytoplasmic', 'num': 760, status: 'public'},

    // private/hidden annotations
    {'name': 'cilia', 'num': 3, status: 'private'},
    {'name': 'diffuse', 'num': 79, status: 'private'},
    {'name': 'textured', 'num': 149, status: 'private'},
    {'name': 'nucleus_cytoplasm_variation', 'num': 117, status: 'private'},
    {'name': 'nucleolar_ring', 'num': 17, status: 'private'},
    {'name': 'peri_golgi', 'num': 0, status: 'private'},
    {'name': 'lysosome', 'num': 0, status: 'private'},
    {'name': 'small_aggregates', 'num': 124, status: 'private'},
];

export const qcCategories = [
    {'name': 'publication_ready', 'num': 1361},
    {'name': 'no_gfp', 'num': 360},
    {'name': 'interesting', 'num': 375},
    {'name': 'pretty', 'num': 221},
    {'name': 'low_gfp', 'num': 254},
    {'name': 'salvageable_re_sort', 'num': 139},
    {'name': 'heterogeneous_gfp', 'num': 139},
    {'name': 'low_hdr', 'num': 129},
    {'name': 're_image', 'num': 67},
    {'name': 'disk_artifact', 'num': 37},
    {'name': 'cross_contamination', 'num': 19},
];


// the 20 most common target families
export const targetFamilies = [
    {'name': 'kinase', 'num': 179},
    {'name': 'SLC', 'num': 74},
    {'name': 'chaperone', 'num': 52},
    {'name': 'endocytosis', 'num': 50},
    {'name': 'proteasome', 'num': 43},
    {'name': 'motor', 'num': 39},
    {'name': 'Diana', 'num': 39},
    {'name': 'transport', 'num': 38},
    {'name': 'BAR', 'num': 35},
    {'name': 'nuclear transport', 'num': 34},
    {'name': 'ER', 'num': 34},
    {'name': 'GEF', 'num': 33},
    {'name': 'PIP metabolism', 'num': 33},
    {'name': 'GAP', 'num': 31},
    {'name': 'positive control', 'num': 30},
    {'name': 'orphan', 'num': 29},
    {'name': 'RNA binding', 'num': 29},
    {'name': 'SNARE', 'num': 28},
    {'name': 'Peter Tuhl', 'num': 25},
    {'name': 'centrosome', 'num': 23},
];


export function categoryNameToLabel (categoryName) {
    // create a prettified label from a category name

    // category labels that cannot be generated programmatically from the category names
    const customCategoryLabels = {
        er: 'ER',
        nucleolus_gc: 'Nucleolus - GC',
        nucleolus_fc_dfc: 'Nucleolus - FC/DFC',
        nucleus_cytoplasm_variation: 'Nucleus-cytoplasm variation',
        big_aggregates: 'Aggregates',
    };

    let label = categoryName.replace(/_/g, ' ');
    return customCategoryLabels[categoryName] || (label.charAt(0).toUpperCase() + label.slice(1));
}
