import React, { useState, useEffect, useContext } from 'react';
import {Popover, Icon} from '@blueprintjs/core';

import { MetadataItem } from './metadata.jsx';
import settings from '../settings/settings.js';
import {cellLineMetadataDefinitions} from '../settings/metadataDefinitions.js';
import * as popoverContents from './popoverContents.jsx';

import './cellLineMetadataTable.scss';


export default function CellLineMetadataTable (props) {
    const modeContext = useContext(settings.ModeContext);

    // metadata items to display in the header for opencell targets
    let targetItemLayouts = [
        {
            id: 'uniprot_id',
            width: 30,
            isPublic: true,
            url: id => `https://www.uniprot.org/uniprot/${id}`,
        },{
            id: 'ensg_id',
            width: 60,
            isPublic: true,
            url: id => `https://uswest.ensembl.org/Homo_sapiens/Gene/Summary?g=${id}`,
        },{
            id: 'target_terminus',
            width: 30,
            isPublic: true,
        },{
            id: 'protospacer_sequence',
            width: 70,
            smaller: true,
            isPublic: true,
        },{
            id: 'protein_concentration',
            width: 49,
            isPublic: true,
            popoverContent: popoverContents.proteinConcentration,
        },{
            id: 'protein_copy_number',
            width: 50,
            isPublic: true,
            popoverContent: popoverContents.proteinCopyNumber,
        },{
            id: 'hdr_all',
            width: 24,
        },{
            id: 'other_all',
            width: 24,
        },{
            id: 'wt_all',
            width: 24,
        },{
            id: 'facs_grade',
            width: 24,
        },{
            id: 'plate_id',
            width: 33,
        },{
            id: 'well_id',
            width: 33,
        },{
            id: 'sort_count',
            width: 33,
        }
    ];

    // TODO: metadata items for interactors (none, for now)

    const interactorItemLayoutIds = [
        'uniprot_id', 'ensg_id', 'protein_concentration', 'protein_copy_number'
    ];
    const interactorItemLayouts = targetItemLayouts.filter(layout =>
        interactorItemLayoutIds.includes(layout.id)
    );

    let itemLayouts = props.isInteractor ? interactorItemLayouts : targetItemLayouts;
    if (modeContext==='public') itemLayouts = itemLayouts.filter(itemLayout => itemLayout.isPublic);

    // warning popovers for cases where protein abundance was imputed or not detected
    const warningIcon = <Icon icon='warning-sign' iconSize={12} color='#e08f3d'/>;
    const imputedProteinAbundanceWarning = (
        <Popover>
            {warningIcon}
            {popoverContents.imputedProteinAbundanceWarning}
        </Popover>
    );
    const undetectedProteinAbundanceWarning = (
        <Popover>
            {warningIcon}
            {popoverContents.undetectedProteinAbundanceWarning}
        </Popover>
    );
    
    const metadataItems = itemLayouts.map(itemLayout => {

        const def = cellLineMetadataDefinitions.filter(def => def.id===itemLayout.id)[0];
        
        let warning = null;
        let units = def.units;
        let value = def.accessor(props.data);

        // for protein concentration and abundance,
        // decide whether to show a warning and override the value if it is NaN
        if (['protein_copy_number', 'protein_concentration'].includes(def.id)) {
            if (props.data.abundance_data?.protein_abundance_imputed) {
                warning = imputedProteinAbundanceWarning;
            }
            else if (value===null) {
                units = '';
                value = 'Not detected';
                warning = undetectedProteinAbundanceWarning;
            }
        }

        return (
            <div
                key={def.id}
                className='pr2 pt1 pb1 clm-item clm-overflow-hidden'
                style={{flex: `0 0 ${itemLayout.width}%`}}
            >
                <MetadataItem
                    scale={5}
                    value={value}
                    units={units}
                    label={def.Header}
                    url={itemLayout.url ? itemLayout.url(def.accessor(props.data)) : undefined}
                    smaller={itemLayout.smaller}
                    popoverContent={itemLayout.popoverContent}
                    warning={warning}
                />
            </div>
        );
    });

    return (
        <div className="flex-wrap items-center pt2 pb3 clm-container">

            {/* protein name */}
            <div className="w-100 blue clm-target-name">
                {props.data.metadata?.target_name}
            </div>

            {/* protein descriptoin */}
            <div className="w-100 pt1 pb2 clm-protein-description">
                {props.data.uniprot_metadata?.protein_name}
            </div>
            {metadataItems}
        </div>
    );
}
