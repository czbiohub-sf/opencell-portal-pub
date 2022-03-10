import React, { Component, useState } from 'react';
import { Link } from 'react-router-dom';
import Callout from '../../components/callout.jsx';

import 'tachyons';
import '../about/about.scss';


const InfoIcon = () => {
    // the SVG for the info icon from blueprintjs, used to show the icon inline w text.
    return (
        <svg class="inline-svg" x="0px" y="0px" viewBox="0 0 16 16">
            <path d="M8 0C3.58 0 0 3.58 0 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zM7 3h2v2H7V3zm3 10H6v-1h1V7H6V6h3v6h1v1z" fill-rule="evenodd"/>
        </svg>
    );
}

export default function Help (props) {
    return (
        <div className='w-100 2 pl5 pr5 pb3 f5 about-page-container'>

            <div className='w-100 pt4 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>How to use this website</div>
                <div className='pt2'>
                    This website provides interactive visualizations of the microscopy images and protein interactions
                    for all 1,310 tagged proteins, or targets, in the OpenCell library.
                    Each of the tagged proteins has a dedicated page, called the "target page,"
                    that displays all of the metadata, microscopy images, 
                    and protein-protein interactions associated with the tagged protein. 
                    There is also a separate dedicated page for each protein in the human proteome
                    that displays the data, if any, that we have collected for that protein
                    as part of the OpenCell project.                     
                </div>
                <div className='pt3 pb3'>
                    <b>There are several ways to start exploring the data:</b>
                    <ul className='ma0'>
                        <li>
                            browse the <Link to='/targets'>list of all tagged proteins</Link>
                        </li>
                        <li>
                            check out the <Link to='/gallery'>gallery of microscopy images</Link>
                        </li>
                        <li>
                            <Link to='/search'>search for a protein</Link> by protein name or keyword
                        </li>
                        <li>
                            visit the <Link to='/help'>data-download</Link> page
                            to learn how to obtain our processed and raw datasets
                        </li>
                    </ul>
                </div>

                <div className='w-100 flex justify-center'>
                    <div className='w-70'>
                    <Callout hideIcon>
                        Look for the <InfoIcon/> icons next to the labels and buttons
                        throughout this website. 
                        Clicking on these icons opens a popup with more information
                        about each part of the website.
                    </Callout>

                    <Callout hideIcon>
                        Please note that this website is currently best viewed using Chrome or Firefox 
                        on a laptop or desktop computer.
                    </Callout>

                    </div>
                </div>
            </div>

            <div className='w-100 pt4 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>The target page</div>
                <div className='pt2 pb4'>
                    This page displays expression data, genotyping data, microscopy images, 
                    and protein interaction data for each of the 1,310 tagged proteins
                    in the OpenCell library.
                    The microscopy images can be zoomed, panned, and visualized in three dimensions.
                    The nodes in the interaction network represent the proteins that interact 
                    with the selected protein; 
                    clicking on a node will link to the corresponding page for that protein. 
                </div>
                <div className=''>
                    <Link to='/target/CID000367'>
                        <img src='/assets/images/how-to-guide-target-page-details.jpg'/>
                    </Link>
                </div>
            </div>

            <div className='w-100 pt4 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>The protein page</div>
                <div className='pt2 pb3'>
                    This page displays generic metadata and HEK293T-specific data 
                    for each protein in the human proteome 
                    that has <b>not</b> yet been tagged as part of the OpenCell project.
                    <ul className='pl5 w-90'>
                    <li>
                    For the ~5,000 proteins that were observed to interact with one or more tagged proteins,
                    this page displays those interactions as both a network visualization and a table. 
                    </li>
                    <li>
                    For the ~10,000 proteins expressed in HEK293T cells, this page displays
                    protein abundance data measured by whole-cell mass spectrometry.
                    </li>
                    <li>
                    For proteins that are not expressed in HEK293T cells,
                    this page displays generic metadata and provides links to external databases. 
                    </li>
                    </ul>
                </div>
                <div className=''>
                <Link to='/gene/ENSG00000198513'>
                    <img width={'100%'} src='/assets/images/how-to-guide-interactor-page-details.jpg'/>
                </Link>
                </div>
            </div>

            <div className='w-100 pt4 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>The gallery page</div>
                <div className='pt2 pb3'>
                    This page displays a grid of thumbnail microscopy images
                    representing all of the tagged proteins in the OpenCell library,
                    filtered by a customizable set of subcellular localization patterns.
                    This page makes it easy to quickly view all of the tagged proteins 
                    that either localize to a specific organelle
                    or that have a specific pattern of multilocalization 
                    (e.g., nucleoplasm and cytoplasm, cytoskeleton and cytoplasm, Golgi and vesicles, etc).
                </div>
                <div className=''>
                    <Link to='/gallery'>
                        <img width={'100%'} src='/assets/images/how-to-guide-gallery-page-details.jpg'/>
                    </Link>
                </div>
            </div>

        </div>
    );
};
