import * as d3 from 'd3';
import React, { Component, useState, useEffect, useContext } from 'react';
import { Icon } from "@blueprintjs/core";
import { useHistory, Link } from 'react-router-dom';

import 'tachyons';
import 'react-table-6/react-table.css';
import "@blueprintjs/core/lib/css/blueprint.css";

import SearchBar from '../../components/searchBar.jsx';
import settings from '../../settings/settings.js';
import Callout from '../../components/callout.jsx';

import './home.scss';

const Stat = props => {
    return (
        <div className='pr3'>
            <div className='f3 b black-80'>{props.value}</div>
            <div className='pt0 f6 black-30'>{props.label}</div>
        </div>
    );
}

const Thumbnail = props => {
    return (
        <div className='home-thumbnail-container'>
            <Link to={`/gallery?localization=${props.localizationCategory || props.label.toLowerCase()}`}>
                <img src={props.src}/>
                <div className='home-thumbnail-container-major-label'>{props.label}</div>
                <div className='home-thumbnail-container-minor-label'>{props.minorLabel}</div>
            </Link>
        </div>
    );
}


export default function Home (props) {
    const history = useHistory();
    const modeContext = useContext(settings.ModeContext);

    // remove blueprint-defined placeholder text in the suggest input elements
    useEffect(() => {d3.selectAll('input').attr('placeholder', '')}, []);

    return (
        <>
        <div className='w-100 home-banner-container'>
            <img src='/assets/images/home_banner_color.png'/>
        </div>

        {/* for some reason, minWidth must be defined on this outer container,
        not the inner home-container (on which a media query defines a max-width);
        otherwise, the left side of the page is cut off on mobile */}
        <div className='w-100 flex justify-center' style={{minWidth: '900px'}}>
            
            <div className='w-100 flex flex-column items-center home-container'>

                <div className='w-50'>
                    <Callout>
                        Check out <a target='_blank' href='https://www.biorxiv.org/content/10.1101/2021.03.29.437450v2'>
                            <b>our preprint</b>
                        </a>  on bioRxiv!
                    </Callout>
                </div>
                
                <div className='w-50'>
                    <Callout>
                        <div className='pl2'>
                            We are hiring! Check out our open positions <Link to='/jobs'><b>here</b></Link>.
                        </div>                        
                    </Callout>
                </div>
                
                {/* top row - title, menu, logo, search textbox */}
                <div className='w-70 pt4 flex flex-column justify-center'>

                    <div className=''>
                        <div className='home-title'><span>OpenCell</span></div>

                        <div className='pt0 pb3 home-title-caption'>
                            <span>
                                Proteome-scale measurements of human protein localization and interactions
                            </span>
                        </div>

                        <div className='flex flex-row justify-around home-menu-container'>
                            <Link to='/targets'>Targets</Link>
                            <Link to='/gallery'>Gallery</Link>
                            <Link to='/download'>Data</Link>
                            <Link to='/help'>Help</Link>
                            <Link to='/about'>About</Link>
                        </div>
                    </div>

                    <div className='pt4 flex justify-center'>
                        <div className='w-30 home-logo-container'>
                            <img src='/assets/images/logos/opencell_logo_v2.png'/>
                        </div>

                        <div className='w-70 pl5'>
                            <div className='pt4 search-bar-container'>
                                <div className='search-bar-caption pb2'>Search for a protein</div>
                                <SearchBar
                                    handleGeneNameSearch={props.handleGeneNameSearch}
                                    history={history}
                                />
                                <div className='pt1 search-bar-hint'>
                                    {'For example: '}
                                    <Link to='/target/CID000828'>MAP4</Link>
                                    {', '}
                                    <Link to='/target/CID000701'>POLR2F</Link>
                                    {', '}
                                    <Link to='/search/chromatin'>chromatin</Link>
                                    {', '}
                                    <Link to='/search/mediator%20complex'>mediator complex</Link>
                                    {''}
                                </div>
                            </div>
                            <div className='pt4 flex justify-around'>
                                <Stat label='Tagged proteins' value={'1,310'}/>
                                <Stat label='Protein interactions' value={'29,922'}/>
                                <Stat label='3D images' value={'5,912'}/>
                            </div>
                        </div>
                    </div>
                </div>

                {/* bottom row - explore by localization */}
                <div className='w-70 pt5 pb5'>
                    <div className='home-thumbnail-container-header'>
                        Explore all tagged proteins by subcellular localization
                    </div>
                    <div className='pt4 flex justify-between'>
                        <Thumbnail
                            label='ER'
                            minorLabel='162 proteins'
                            src='/assets/images/home-thumbnails/BCAP31.jpg'
                        />
                        <Thumbnail
                            label='Golgi'
                            minorLabel='112 proteins'
                            src='/assets/images/home-thumbnails/GOLGA2.jpg'
                        />
                        <Thumbnail
                            label='Mitochondria'
                            minorLabel='16 proteins'
                            src='/assets/images/home-thumbnails/VDAC1.jpg'
                        />
                        
                        <Thumbnail
                            label='Cytoskeleton'
                            minorLabel='60 proteins'
                            src='/assets/images/home-thumbnails/MAP4.jpg'
                        />
                        <Thumbnail
                            label='Centrosome'
                            minorLabel='69 proteins'
                            src='/assets/images/home-thumbnails/CEP131.jpg'
                        />
                    </div>
                    <div className='pt3 flex justify-between'>
                        
                        <Thumbnail
                            label='Nuclear membrane'
                            minorLabel='48 proteins'
                            localizationCategory='nuclear_membrane'
                            src='/assets/images/home-thumbnails/LMNB1.jpg'
                        />

                        <Thumbnail
                            label='Nucleolus (GC)'
                            minorLabel='100 proteins'
                            localizationCategory='nucleolus_gc'
                            src='/assets/images/home-thumbnails/NPM1.jpg'
                        />
                        <Thumbnail
                            label='Nucleolus (FC/DFC)'
                            minorLabel='37 proteins'
                            localizationCategory='nucleolus_fc_dfc'
                            src='/assets/images/home-thumbnails/POLR1B.jpg'
                        />
                        <Thumbnail
                            label='Nuclear punctae'
                            minorLabel='152 proteins'
                            localizationCategory='nuclear_punctae'
                            src='/assets/images/home-thumbnails/TERF1.jpg'
                        />
                        <Thumbnail
                            label='Chromatin'
                            minorLabel='145 proteins'
                            src='/assets/images/home-thumbnails/H2BC21.jpg'
                        />

                    </div>
                    <div className='pt3 flex justify-between'>
                        <Thumbnail
                            label='Nucleoplasm'
                            minorLabel='674 proteins'
                            src='/assets/images/home-thumbnails/WEE1.jpg'
                        />
                        <Thumbnail
                            label='Cytoplasm'
                            minorLabel='760 proteins'
                            localizationCategory='cytoplasmic'
                            src='/assets/images/home-thumbnails/RELA.jpg'
                        /> 
                        <Thumbnail
                            label='Plasma membrane'
                            minorLabel='191 proteins'
                            localizationCategory='membrane'
                            src='/assets/images/home-thumbnails/RAC1.jpg'
                        />
                        <Thumbnail
                            label='Vesicles'
                            minorLabel='394 proteins'
                            src='/assets/images/home-thumbnails/CLTA.jpg'
                        />
                        <Thumbnail
                            label='Focal adhesions'
                            minorLabel='13 proteins'
                            localizationCategory='focal_adhesions'
                            src='/assets/images/home-thumbnails/PXN.jpg'
                        />
                    </div>

                </div>

            </div>
        </div>

        </>
    );
}
