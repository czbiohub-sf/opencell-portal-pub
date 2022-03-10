
import React, { Component, useState } from 'react';
import { Link } from 'react-router-dom';

import 'tachyons';
import 'react-table-6/react-table.css';
import "@blueprintjs/core/lib/css/blueprint.css";

import CellGraphic from './CellGraphic.jsx';
import Callout from '../../components/callout.jsx';

import './about.scss';


const Lightbox = props => {
    const [visible, setVisible] = useState(false);
    const lightboxContainer = (
        <div className='howto-lightbox-container' onClick={() => setVisible(false)}>
            <div className='pa3 bg-white br4'>
                <div className='w-100 f2 b tc'>{props.title}</div>
                {props.children}
            </div>
        </div>
    );
    const childContainer = (
        <div className={props.className} onClick={() => setVisible(true)}>{props.children}</div>
    );
    return visible ? lightboxContainer : childContainer;
};


export default function About (props) {
    return (
        <div className='w-100 pt4 pl5 pr5 pb3 f5 about-page-container'>

            {/* first row - logo and welcome blurb */}
            <div className='w-100 pl5 pr5 flex items-top'>

                {/* large opencell logo - hard-coded width to match the SVG width */}
                <div className='pr5 pt3' style={{width: '300px'}}>
                    <CellGraphic/>
                </div>

                {/* welcome blurb */}
                <div className='w-60 pl3'>
                    <div className='w-100 f2'>About OpenCell</div>
                    <div className='w-100 pt2'>
                        <p>
                            OpenCell is a proteome-scale collection of protein localization 
                            and interaction measurements in human cells.
                            It is built upon a library of 1,310 endogenously-tagged HEK293T cell lines 
                            that enables us to observe both protein localization
                            (using live-cell fluorescence microscopy) 
                            and protein-protein interactions (using IP-MS) in the same cellular context.
                        </p>
                        <p>                            
                            This project is a collaboration between 
                            the <a href='https://www.czbiohub.org/manuel-leonetti-intracellular-architecture/'>
                                Leonetti Lab
                            </a> at the Chan Zuckerberg Biohub and 
                            the <a href='https://www.biochem.mpg.de/mann'>Mann Lab</a> at
                            the Max Plank Institute for Biochemistry, along with many other collaborators.
                        </p>

                        <p>
                            For experimental details about the OpenCell library, please see the description below,
                            and checkout our preprint for more information.
                            For information about how to download the data, 
                            please see the <Link to='/download'>data-download page</Link>. 
                        </p>
                        <Callout>
                            Check out <a target='_blank' href='https://www.biorxiv.org/content/10.1101/2021.03.29.437450v2'>
                                <b>our preprint</b>
                            </a>  on bioRxiv!
                        </Callout>
                        <Callout>
                            We welcome feedback!<br></br>
                            Please <Link to='/contact'><b>contact us</b></Link> if you have questions or comments.
                        </Callout>

                    </div>
                </div>
            </div>

            <div className='w-100 pt3 flex justify-center'>
                <div className='w-90'>
                    <div className='w-100 ml3 f3 bb b--black-30'>About the OpenCell library</div>
                    <div className='pt2'>
                        <img src='/assets/images/about-page-figure.png'/>
                    </div>
                    <div className='pt2 w-100 ml3'>
                    <p>
                    The OpenCell library of fluorescently tagged HEK293T cell lines was constructed 
                    by tagging human genes with a split-fluorescent-protein system
                    based on mNeonGreen2 (<a href='https://www.nature.com/articles/s41467-017-00494-8' target='_blank'>Feng et al., 2017</a>).
                    FP insertion sites (N or C terminus) were chosen
                    on the basis of information from the literature or structural analysis.
                    For each tagged target, we isolated a polyclonal pool of CRISPR-edited cells, 
                    which was then characterized by live-cell three-dimensional
                    (3D) confocal microscopy, IP-MS, and genotyping of tagged alleles 
                    by next-generation sequencing.
                    </p>
                    <p>
                    In total, we have tagged 1,757 genes, of which 1,310 (75%) could be detected 
                    by fluorescence microscopy and form the basis of the data displayed on this website. 
                    The 1,310-protein collection is a balanced representation of the human proteome, 
                    with the exception of proteins specific to mitochondria,
                    organellar lumen, or extracellular matrix, which are not accessible
                    using our current split-FP system. 
                    </p>
                    <p>
                    To maximize throughput, we used a polyclonal strategy to select genome-edited cells by FACS.
                    This approach yielded polyclonal pools containing cells with distinct genotypes. 
                    The library of 1,310 tagged cell lines has a median 61% of mNeonGreen-integrated alleles,
                    5% wildtype, and 26% non-functional alleles.
                    Because non-functional alleles do not support fluorescence,
                    they are unlikely to have an impact on other measurements, 
                    especially in the context of a polyclonal population. 
                    </p>
                    <p>
                    Fluorescent tagging was readily successful for essential genes, 
                    which suggests that FP fusions are well tolerated.
                    To verify that our approach does not perturb endogenous expression levels,
                    we quantified protein expression by Western blotting 
                    using antibodies specific to proteins targeted in 12 tagged lines
                    and by single-shot mass spectrometry in 63 tagged lines.
                    Both approaches revealed a median abundance of tagged targets 
                    in engineered lines at ~80% of untagged HEK293T control. 
                    The overall proteome composition was unchanged in all tagged lines.
                    </p>
                    <p className='tc b'>
                        For much more information, please check out <a target='_blank' href='https://www.biorxiv.org/content/10.1101/2021.03.29.437450v2'>
                            <b>our preprint</b>
                        </a> on bioRxiv!
                    </p>

                    </div>
                </div>
            </div>

        </div>
    );
};


