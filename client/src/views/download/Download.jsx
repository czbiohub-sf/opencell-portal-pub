import React, { Component, useState } from 'react';
import { Link } from 'react-router-dom';

import settings from '../../settings/settings.js';
import 'tachyons';
import '../about/about.scss';


function DatasetLinks (props) {
    const dataUrl = settings.apiUrl.replace('/api', '/data');
    return (
        <div className='w-100 flex items-left flex-column' style={{lineHeight: 1}}>
            <div className='f4'>{props.title}</div>
            <div className='pl0'>
                <a href={`${dataUrl}/datasets/${props.filename}.xlsx`}>Excel</a>
                <span className='f3'>  ·  </span>
                <a href={`${dataUrl}/datasets/${props.filename}.csv`}>CSV</a>
                <span className='f3'>  ·  </span>
                <a href={`${dataUrl}/datasets/${props.filename}-readme.csv`}>README</a>
            </div>
        </div>
    );
}

export default function Download (props) {
    return (

        <div className='w-100 pt4 flex flex-row justify-center download-page-container'>
            
            <div className='w-70'>
            
            <div>
                <div className='w-100 f3 bb b--black-30'>Data downloads</div>
                <div className='w-100 pt2 f5'>
                    All of the data displayed on this website are available for download,
                    along with the underlying raw mass-spectrometry and microscopy data.
                    Please <Link to="./contact">contact us</Link> if you encounter any trouble accessing these datasets
                    or discover any issues or inconsistencies in them. 
                </div>
            </div>

            <div className='pt4'>
                <div className='w-100 f3 bb b--black-30'>Processed datasets</div>
                <div className='w-100 pt2 pb3 f5'>
                    These datasets contain aggregated metadata and processed data
                    for all tagged proteins in the OpenCell library, 
                    all protein-protein interactions detected by IP-MS, 
                    and protein abundance measurements for the entire HEK293T proteome. 
                    Please note that while these datasets contain much of the same data 
                    found in the supplementary tables from our <a href=''>2022 publication</a>, 
                    the datasets provided here will be updated over time as new data is generated. 
                </div>

                <DatasetLinks title='Library metadata' filename='opencell-library-metadata'/>
                <div className='pt2 pb4 f5'>
                    Metadata and quality-control metrics for all 1,310 tagged cell lines in the OpenCell library. 
                    This includes Ensembl gene and transcript IDs,
                    insertion sites, protospacer and donor sequences used for the CRISPR insertions,
                    and genotyping results. 
                </div>

                <DatasetLinks title='Protein abundance' filename='opencell-protein-abundance'/>
                <div className='pt2 pb4 f5'>
                    This dataset contains transcript expression levels (measured by RNA-Seq)
                    and estimates of absolute protein abundance (measured by whole-cell mass spectrometry)
                    for all proteins expressed in HEK293T cells.
                    The estimates of protein abundance are derived from the mass-spectrometric intensities
                    using the approach described 
                    in <a href='https://www.sciencedirect.com/science/article/pii/S1535947620337749' target='_blank'>
                        Wisniewski et al., 2014
                    </a>.
                    Absolute values were obtained by normalizing with empirical estimates
                    of 200pg for the total protein mass per cell and 1pL for the cellular volume
                    of HEK293T cells. 
                    Note that accuracy of these estimates is difficult to quantify for individual proteins,
                    but is, on average, within a factor of two. 
                </div>

                <DatasetLinks title='Protein-protein interactions' filename='opencell-protein-interactions'/>
                <div className='pt2 pb4 f5'>
                    This dataset contains the statistically significant protein-protein interactions 
                    detected in all 1,260 OpenCell IP-MS experiments, along with their enrichments
                    and interaction stoichiometries. Please refer to
                    the supplementary methods from our <a href=''>2022 publication</a> for
                    details about the experimental and computational methods used to obtain these results.
                </div>

                <DatasetLinks title='Protein localization annotations' filename='opencell-localization-annotations'/>
                <div className='pt2 pb4 f5'>
                    This dataset contains the manually-assigned subcellular localization categories 
                    for each tagged protein in the OpenCell library. 
                    Each category is divided into three 'grades':
                    grade 3 indicates a very prominent localization,
                    grade 2 indicates unambiguous but less prominent localization, 
                    and grade 1 indicates weak or barely detectable localization. 
                    Please note that these annotations are necessarily subjective 
                    and should be interpreted accordingly. 
                    However, we have shown that our annotations are broadly consistent 
                    with independent reference datasets. 
                </div>

                <div className='w-100 f3 bb b--black-30'>Raw datasets</div>
                <div className='w-100 pt2 pb3 f5'>
                    The raw mass spectra and raw microscopy data are available for download
                    from third-party repositories. Please note that these datasets are large. 
                    Details about how to download subsets of the data are provided below. 
                </div>

                <div className='w-100 flex items-left flex-column' style={{lineHeight: 1}}>
                    <div className='f4'>Raw protein abundance data</div>
                    <div className=''>
                        <a href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE186192' target='_blank'>
                            GEO GSE186192 (bulk RNA-Seq)
                        </a>
                        <span className='f3'>  ·  </span>
                        <a href='https://www.ebi.ac.uk/pride/archive/projects/PXD029191' target='_blank'>
                            PRIDE PXD029191 (whole-cell MS)
                        </a>
                    </div>
                </div>
                <div className='pt2 pb4 f5'>
                    Protein abundance in HEK293T cells was measured using bulk RNA-Seq 
                    and whole-cell mass spectrometry.
                    Processed results from these datasets 
                    (including the estimates of absolute protein concentration and copy number)
                    are found in the "Protein abundance" dataset above. 
                </div>

                <div className='w-100 flex items-left flex-column' style={{lineHeight: 1}}>
                    <div className='f4'>Raw IP-MS data</div>
                    <div className=''>
                        <a href='https://www.ebi.ac.uk/pride/archive/projects/PXD024909' target='_blank'>
                            PRIDE PXD024909
                        </a>
                        <span className='f3'> </span>
                    </div>
                </div>
                <div className='pt2 pb4 f5'>
                    The raw mass spectrometry data includes raw spectra and associated MaxQuant output tables
                    for the complete set of IP-MS experiments (that is, the 1,260 OpenCell target pulldowns). 
                    This data was used to generate the OpenCell interactome 
                    found in the "Protein-protein interactions" dataset above.
                </div>

                <div className='w-100 f4 bb b--black-30'>Raw microscopy images</div>
                <div className='pt2 f5'>
                    The raw confocal microscopy images for all OpenCell targets are available as 16-bit TIFF files. 
                    These files are hosted in a public AWS S3 bucket 
                    called <code>
                        <a href="https://czb-opencell.s3.amazonaws.com/index.html#microscopy/raw/" target="_blank">czb-opencell</a>
                    </code> provided by 
                    the <a href="https://aws.amazon.com/opendata" target="_blank">AWS Open Data program</a>.
                    There are between four and six images for each of the 1,310 targets; 
                    the entire dataset contains 6,301 images.
                    <br></br><br></br>
                    
                    There are two TIFF files associated with each image: 
                    a two-dimensional maximum-intensity z-projection 
                    and the original three-dimensional confocal z-stack.
                    In both cases, there are two fluorescence channels in each TIFF file. 
                    The first channel is the signal from the Hoechst staining 
                    (this is a live-cell DNA dye that serves as a fiducial marker for the cell nuclei)
                    and the second channel is the signal from the tagged protein itself. 
                    <br></br><br></br>
                    
                    The TIFF files are organized into target-specific subdirectories with 
                    names of the form <code>{`<gene-name>_<ensg-id>`}</code>. 
                    For example, all raw TIFFs for the target ATL3 are found in this directory:
                    <pre>s3://czb-opencell/microscopy/raw/ATL3_ENSG00000184743</pre>

                    The filenames of the raw TIFFs are composed of underscore-separated metadata fields 
                    in the following format:
                    <pre>{`OC-FOV_<gene-name>_<ensg-id>_<cell-line-id>_<fov-id>_<stack|proj>.tif`}</pre>

                    All of the filenames begin with the common prefix <code>'OC-FOV'</code> (
                    this stands for 'OpenCell field of view').  
                    The gene name and ENSG ID identify the target protein - 
                    that is, the protein that is fluorescently tagged in the images.  
                    Please note that the gene name is included only for human readibility 
                    and is not guaranteed to be stable or unique.
                    For this reason, 
                    <b> only the ENSG ID can be used to unambiguously identify each tagged protein. </b>
                    In addition to the ENSG ID, there are two internal IDs - a cell line ID and an FOV ID. 
                    These IDs do not encode any meaningful technical or biological information, 
                    though the FOV ID may be used as a globally unique identifier for each image. 
                    Finally, the <code>'stack'</code> or <code>'proj'</code> appendix 
                    differentiates between z-stacks and z-projections.
                    <br></br><br></br>
                    For example, this is the filename of the raw z-projection for one of the images of ATL3:
                    <pre>OC-FOV_ATL3_ENSG00000184743_CID000367_FID00030311_proj.tif</pre>


                    There are several ways to download these raw TIFFs (none of which require an AWS account):
                    <ul className='about-page-bullets'>
                        <li>
                            To download the raw TIFF for a selected FOV on the target page of this website,
                            click the "Download raw" button at the top right corner of the image viewer. 
                        </li>
                        <li>
                            To explore the S3 bucket itself, use 
                            the <a href="https://czb-opencell.s3.amazonaws.com/index.html" target="_blank"> 
                                interactive web-based viewer
                            </a>.
                            This interface can also be used to manually download individual files. 
                        </li>
                        <li>
                            To programmatically download the entire set (or a subset) of the raw TIFFs, 
                            use 
                            the <a href="https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3/index.html" target="_blank">
                                AWS S3 CLI
                            </a>. 
                            If you do not have an AWS account, 
                            include the <code>--no-sign-request</code> flag in your command.
                            For example, this command downloads all of the raw z-projections for ATL3:
                            <pre>
                                aws s3 cp s3://czb-opencell/microscopy/raw/ /some/local/directory/ \<br></br>
                                --recursive --no-sign-request --exclude "*" --include "*_ATL3_*proj.tif"
                            </pre>
                            A note about filesizes: 
                            each raw z-projection is 1.4MB and each raw z-stack is between 100-150MB,
                            depending on the depth of the stack. 
                            The entire dataset contains 6,301 images and is approximately 1TB in size.
                        </li>
                    </ul>
                </div>


            </div>
        </div>
        </div>
    );
};
