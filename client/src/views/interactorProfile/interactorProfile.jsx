
import * as d3 from 'd3';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Callout } from '@blueprintjs/core';

import 'tachyons';
import 'react-table-6/react-table.css';
import "@blueprintjs/core/lib/css/blueprint.css";

import ExpressionPlot from '../../components/expressionPlot.jsx';
import MassSpecContainer from '../../components/massSpecContainer.jsx';
import CellLineMetadataTable from '../../components/cellLineMetadataTable.jsx';
import ExternalLinks from '../../components/externalLinks.jsx';
import SectionHeader from '../../components/sectionHeader.jsx';
import FunctionalAnnotation from '../../components/functionalAnnotation.jsx';
import settings from '../../settings/settings.js';
import * as popoverContents from '../../components/popoverContents.jsx';


export default function InteractorProfile (props) {

    const [geneMetadata, setGeneMetadata] = useState({});
    const [isLoaded, setLoaded] = useState(false);

    // load the metadata for the interactor
    // TODO: this request is only needed for the interactor's metadata, 
    // not for the interactors themselves (which are loaded in the MassSpecContainer)
    useEffect(() => {
        setLoaded(false);
        if (!props.match.params.ensgId) return;
        d3.json(`${settings.apiUrl}/interactors/${props.match.params.ensgId}`).then(data => {
            setGeneMetadata(data); 
            setLoaded(true); 
        }, error => setLoaded(false));
    }, [props.match]);

    const hasInteractors = geneMetadata?.metadata?.has_interactors;
    const isExpressed = geneMetadata?.metadata?.is_expressed;

    const NotExpressedCallout = (
        <Callout 
            title='This protein was not found to be expressed in HEK293T cells' 
            intent='warning' 
            showHeader={true}
        >
            This protein was not found to be expressed in HEK293T cells by bulk RNA-Seq.
            Note that protein expression was defined using a threshold of 1 transcript per million.
            If you believe this may be an error, please <Link to='/contact'>contact us</Link>.
        </Callout>
    );

    const ExpressedButNoInteractorsCallout = (
        <Callout 
            title='This protein was not observed to interact with any OpenCell targets' 
            intent='warning' 
            showHeader={true}
        >
            Although this protein was found to be expressed in HEK293T cells, 
            no interactions were detected between it
            and any of the 1,310 tagged proteins in the current OpenCell library. 
            Stay tuned while we increase the size of our library! 
            In the meantime, our estimates of abundance for this protein are reported below.
            If you feel that this protein should be prioritized for tagging, 
            please <Link to='/contact'>let us know</Link>!
        </Callout>
    );


    const InteractorCallout = (
        <Callout 
            title='The interaction network for this protein is incomplete' 
            intent='warning' 
            showHeader={true}
        >
            Although this protein was not tagged as part of the OpenCell project, 
            it was observed to interact with one or more of the tagged proteins in the OpenCell library. 

            This means that the protein interactions shown below 
            correspond <b>only</b> to the tagged proteins that were observed to interact with this protein. 
            They are therefore almost certainly incomplete. 
        </Callout>
    );

    return (
        <>
            <div className='pl5 pr5 pt3 pb1 flex justify-center'>
                <div className='w-80'>
                    <Callout 
                        title='This protein is not in the OpenCell library' 
                        intent='warning' 
                        showHeader={true}
                    >
                        This protein has not yet been tagged as part of the OpenCell project.

                        This page displays all of the data we have collected for this protein,
                        which may include its abundance in HEK293T cells 
                        (measured by whole-cell mass spectrometry)
                        and its interactions with targets in the OpenCell library (measured by IP-MS). 
                    </Callout>
                    
                    {(isLoaded && hasInteractors) ? <div className='pt3'>{InteractorCallout}</div> : null}

                    {(isLoaded && !isExpressed) ? <div className='pt3'>{NotExpressedCallout}</div> : null}

                    {(isLoaded && isExpressed && !hasInteractors) ? <div className='pt3'>{ExpressedButNoInteractorsCallout}</div> : null}
                </div>
            </div>

            {/* main container */}
            <div className="pl3 pr3 flex">

                {/* Left column */}
                <div className="pl2 pr2" style={{width: '350px'}}>
                    <CellLineMetadataTable data={geneMetadata} isInteractor/>
                    <SectionHeader 
                        title='About this protein'
                        popoverContent={popoverContents.aboutThisProteinHeader}
                    />
                    <FunctionalAnnotation content={geneMetadata.uniprot_metadata?.annotation}/>
                    <SectionHeader 
                        title='Reference databases'
                        popoverContent={popoverContents.referenceDatabasesHeader}
                    />
                    <ExternalLinks data={geneMetadata}/>

                    {/* protein abundance scatterplot*/}
                    <SectionHeader
                        title='Protein abundance'
                        popoverContent={popoverContents.expressionLevelHeader}
                    />
                    <div className="w-100 pb3 expression-plot-container">
                        <ExpressionPlot
                            rnaAbundance={geneMetadata.abundance_data?.rna_abundance}
                            proteinAbundance={geneMetadata.abundance_data?.protein_concentration}
                        />
                    </div>

                </div>

                {/* right column - mass spec network/table */}
                <div className="w-60 pt4 pl3">
                    <SectionHeader
                        title='Protein-protein interactions'
                        popoverContent={popoverContents.massSpecInteractorPageHeader}
                    />
                    <MassSpecContainer
                        layout='tabs'
                        ensgId={geneMetadata.metadata?.ensg_id}
                        geneName={geneMetadata.metadata?.target_name}
                        handleGeneNameSearch={props.handleGeneNameSearch}
                    />
                </div>
            </div>
        {isLoaded ? (null) : (<div className='loading-overlay'/>)}
        </>
    );
}
