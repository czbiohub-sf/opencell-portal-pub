import * as d3 from 'd3';
import React, { useState, useEffect, useContext } from 'react';

import CellLineTable from '../../components/cellLineTable.jsx';
import TargetProfileOverview from './targetProfileOverview.jsx';
import FovAnnotator from './fovAnnotator.jsx';
import settings from '../../settings/settings.js';

import 'tachyons';
import '@blueprintjs/core/lib/css/blueprint.css';
import './targetProfile.scss';


export default function TargetProfile (props) {

    const modeContext = useContext(settings.ModeContext);
    const [cellLine, setCellLine] = useState(null);

    // load the metadata for all cell lines
    useEffect(() => {
        setCellLine(null);
        if (!props.cellLineId) return;
        const url = `${settings.apiUrl}/lines/${props.cellLineId}?publication_ready=${modeContext==='public'}`;
        d3.json(url).then(data => setCellLine(data));
    }, [props.cellLineId])

    // update the cellLineId when the user clicks the back or forward buttons
    // (this effect also runs after calls to history.push)
    useEffect(() => {
        const cellLineIdFromUrl = props.match.params.cellLineId;
        props.setCellLineId(cellLineIdFromUrl, false);
    }, [props.match]);

    let content;
    if (props.showFovAnnotator) {
        content = <FovAnnotator cellLineId={props.cellLineId} cellLine={cellLine}/>
    } else {
        content = (
            <TargetProfileOverview
                cellLine={cellLine}
                cellLineId={props.cellLineId}
                handleGeneNameSearch={props.handleGeneNameSearch}
                showTargetAnnotator={props.showTargetAnnotator}
            />
        );
    }

    return (
        <>
            {/* main container */}
            <div className="pl3 pr3" style={{width: '1600px'}}>
                {cellLine ? content : null}
            </div>

            {/* table of all targets */}
            {
                modeContext==='private' ? (
                    <div className='pt3 pb2'>
                        <CellLineTable cellLineId={props.cellLineId} setCellLineId={props.setCellLineId}/>
                    </div>
                ) : null
            }

            {/* loading modal */}
            {cellLine ? null : <div className='f2 tc loading-overlay'>Loading...</div>}
        </>
    );
}
