**************************
* HGNC genenamesorg data *
**************************
----------------------------------------------------------------------------
All data within this FTP server is freely available without any restrictions
----------------------------------------------------------------------------

Within this FTP directory we maintain files that reflect the data that we
provide via our website http://www.genenames.org. We maintain an old file
format that we do not recommend using if downloading our data for the first
time, and a two new file formats which we strongly suggest using. Since there
are many users and institutes that still use the older formats we have decided
to maintain these files in the same paths but point people to use the new
files. Below are all the directories that contain the new (easier to parse)
files.

HCOP data ftp://ftp.ebi.ac.uk/pub/databases/genenames/hcop/
===========================================================

For your convenience we have pre-calculated some files of HCOP data. You have
the option of getting a file containing human and ortholog data from a single
species, or human and ortholog data from all HCOP species in a single file.
For the human - single ortholog species files the '6 Column' output returns
the raw assertions, Ensembl gene IDs and Entrez Gene IDs for human and one
other species, while the '15 Column' output includes additional information
such as the chromosomal location, accession numbers and where possible
references the approved gene nomenclature.

The files containing all species ortholog data have an additional column at
the start giving the taxon id for each ortholog species.


Gene symbol reports
===================

JSON format files ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/json
----------------------------------------------------------------------

alternative_loci_set.json    Complete set of all approved gene symbol reports
                             found on alternative reference loci (GRCh38)of
                             the human genome.

alternative_loci_chr_*.json  Approved gene symbol reports found at alternative
                             reference loci by chromosome.

hgnc_complete_set.json       Complete set of all approved gene symbol reports
                             found on the GRCh38 reference and the alternative
                             reference loci.

non_alt_loci_set.json        Complete set of all approved gene symbol reports
                             found on the reference assembly (GRCh38) and not
                             on alternative reference loci.

non_alt_loci_set_chr_*.json  Approved gene symbol reports per GRCh38
                             chromosome. Does not contain genes found on
                             alternative reference loci chromosomes.

withdrawn.json               A file containing all gene symbol reports that
                             are no longer approved. Either the symbol has
                             been withdrawn or merged/split into other report

locus_groups/                This directory contains gene symbol report files
                             split by our locus groups and file that are split
                             by locus group and chromosome.

locus_types/                 This directory contains gene symbol report files
                             split by our locus types and file that are split
                             by locus type and chromosome.



TSV (tab separated files) ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv
-----------------------------------------------------------------------------

alternative_loci_set.txt     Complete set of all approved gene symbol reports
                             found on alternative reference loci (GRCh38)of
                             the human genome.

alternative_loci_chr_*.txt   Approved gene symbol reports found at alternative
                             reference loci by chromosome.

hgnc_complete_set.txt        Complete set of all approved gene symbol reports
                             found on the GRCh38 reference and the alternative
                             reference loci.

non_alt_loci_set.txt         Complete set of all approved gene symbol reports
                             found on the reference assembly (GRCh38) and not
                             on alternative reference loci.

non_alt_loci_set_chr_*.txt   Approved gene symbol reports per GRCh38
                             chromosome. Does not contain genes found on
                             alternative reference loci chromosomes.

withdrawn.txt                A file containing all gene symbol reports that
                             are no longer approved. Either the symbol has
                             been withdrawn or merged/split into other report

locus_groups/                This directory contains gene symbol report files
                             split by our locus groups and file that are split
                             by locus group and chromosome.

locus_types/                 This directory contains gene symbol report files
                             split by our locus types and file that are split
                             by locus type and chromosome.

Fields within the tsv and JSON files
------------------------------------

hgnc_id                  = HGNC ID. A unique ID created by the HGNC for every
                           approved symbol.

symbol                   = The HGNC approved gene symbol. Equates to the
                           "APPROVED SYMBOL" field within the gene symbol
                           report.

name                     = HGNC approved name for the gene. Equates to the
                           "APPROVED NAME" field within the gene symbol report.

locus_group              = A group name for a set of related locus types as
                           defined by the HGNC (e.g. non-coding RNA).

locus_type               = The locus type as defined by the HGNC (e.g. RNA,
                           transfer).

status                   = Status of the symbol report, which can be either
                           "Approved" or "Entry Withdrawn".

location                 = Cytogenetic location of the gene (e.g. 2q34).

location_sortable        = Same as "location" but single digit chromosomes are
                           prefixed with a 0 enabling them to be sorted in
                           correct numerical order (e.g. 02q34).

alias_symbol             = Other symbols used to refer to this gene as seen in
                           the "SYNONYMS" field in the symbol report.

alias_name               = Other names used to refer to this gene as seen in
                           the "SYNONYMS" field in the gene symbol report.

prev_symbol              = Symbols previously approved by the HGNC for this
                           gene. Equates to the "PREVIOUS SYMBOLS & NAMES" field
                           within the gene symbol report.

prev_name                = Gene names previously approved by the HGNC for this
                           gene. Equates to the "PREVIOUS SYMBOLS & NAMES" field
                           within the gene symbol report.

gene_group               = Name given to a gene family or group the gene has been
                           assigned to. Equates to the "GENE FAMILY" field within
                           the gene symbol report.

gene_group_id            = ID used to designate a gene family or group the gene
                           has been assigned to.

date_approved_reserved   = The date the entry was first approved.

date_symbol_changed      = The date the gene symbol was last changed.

date_name_changed        = The date the gene name was last changed.

date_modified            = Date the entry was last modified.

entrez_id                = Entrez gene ID. Found within the "GENE RESOURCES"
                           section of the gene symbol report.

ensembl_gene_id          = Ensembl gene ID. Found within the "GENE RESOURCES"
                           section of the gene symbol report.

vega_id                  = Vega gene ID. Found within the "GENE RESOURCES"
                           section of the gene symbol report.

ucsc_id                  = UCSC gene ID. Found within the "GENE RESOURCES"
                           section of the gene symbol report.

ena                      = International Nucleotide Sequence Database
                           Collaboration (GenBank, ENA and DDBJ) accession
                           number(s). Found within the "NUCLEOTIDE SEQUENCES"
                           section of the gene symbol report.

refseq_accession         = RefSeq nucleotide accession(s). Found within the
                           "NUCLEOTIDE SEQUENCES" section of the gene symbol
                           report.

ccds_id                  = Consensus CDS ID. Found within the
                           "NUCLEOTIDE SEQUENCES" section of the gene symbol
                           report.

uniprot_ids              = UniProt protein accession. Found within the
                           "PROTEIN RESOURCES" section of the gene symbol
                           report.

pubmed_id                = Pubmed and Europe Pubmed Central PMID(s).

mgd_id                   = Mouse genome informatics database ID. Found within
                           the "HOMOLOGS" section of the gene symbol report.

rgd_id                   = Rat genome database gene ID. Found within the
                           "HOMOLOGS" section of the gene symbol report.

lsdb                     = The name of the Locus Specific Mutation Database and
                           URL for the gene separated by a | character

cosmic                   = Symbol used within the Catalogue of somatic
                           mutations in cancer for the gene.

omim_id                  = Online Mendelian Inheritance in Man (OMIM) ID

mirbase                  = miRBase ID

homeodb                  = Homeobox Database ID

snornabase               = snoRNABase ID

bioparadigms_slc         = Symbol used to link to the SLC tables database at
                           bioparadigms.org for the gene

orphanet                 = Orphanet ID

pseudogene.org           = Pseudogene.org

horde_id                 = Symbol used within HORDE for the gene

merops                   = ID used to link to the MEROPS peptidase database

imgt                     = Symbol used within international ImMunoGeneTics
                           information system

iuphar                   = The objectId used to link to the IUPHAR/BPS Guide to
                           PHARMACOLOGY database. To link to IUPHAR/BPS Guide
                           to PHARMACOLOGY database only use the number
                           (only use 1 from the result objectId:1)

kznf_gene_catalog        = ID used to link to the Human KZNF Gene Catalog

mamit-trnadb             = ID to link to the Mamit-tRNA database

cd                       = Symbol used within the Human Cell Differentiation
                           Molecule database for the gene

lncrnadb                 = lncRNA Database ID

enzyme_id                = ENZYME EC accession number

intermediate_filament_db = ID used to link to the Human Intermediate Filament
                           Database

agr                      = The HGNC ID that the Alliance of Genome Resources
                           (AGR) have linked to their record of the gene. Use
                           the HGNC ID to link to the AGR.

lncipedia                = The gene symbol used to link to LNCipedia - a
                           comprehensive compendium of human long non-coding
                           RNAs.

mane_select              = NCBI and Ensembl transcript IDs/acessions
                           including the version number for one high-quality
                           representative transcript per protein-coding gene
                           that is well-supported by experimental data and
                           represents the biology of the gene. The IDs are
                           delimited by |.

gencc                    = The HGNC ID used within the GenCC database as the
                           unique identifier of their gene reports within the
                           GenCC database.

LSDB Links file
===============
ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/lsdb_links.txt.gz

File containing LSDB links per gene.

New gene family files
=====================
ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/genefamilies.txt
File containing all the new gene families in a tab separated format.

ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/json/genefamilies.json
File containing all the new gene families in a JSON format.
