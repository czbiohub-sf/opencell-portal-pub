import React, { useState, useEffect, useContext } from 'react';
import {cellLineMetadataDefinitions} from '../settings/metadataDefinitions.js';

import './externalLinks.scss';

export default function ExternalLinks (props) {
    // note that external links are the same for both targets and interactors

    const linkLayouts = [
        {
            id: 'ensg',
            defId: 'ensg_id',
            width: 30,
            label: 'Ensembl',
            url: id => `https://uswest.ensembl.org/Homo_sapiens/Gene/Summary?g=${id}`,
        },{
            id: 'entrez',
            defId: 'ensg_id',
            width: 30,
            label: 'Entrez',
            url: id => `https://www.ncbi.nlm.nih.gov/gene/?term=${id}`
        },{
            id: 'uniprot',
            defId: 'uniprot_id',
            width: 30,
            label: 'UniProt',
            url: id => `https://www.uniprot.org/uniprot/${id}`,
        },{
            id: 'hpa',
            defId: 'ensg_id',
            width: 30,
            label: 'HPA',
            url: id => `https://www.proteinatlas.org/${id}`,
        }
    ];

    const linkItems = linkLayouts.map((item, ind) => {
        const def = cellLineMetadataDefinitions.filter(def => def.id===item.defId)[0];
        const value = def.accessor(props.data);
        return (
            <React.Fragment key={item.id}>
                <a className='f6 pr3' href={item.url(value)} target='_blank'>
                    {item.label}
                </a>
                {ind < (linkLayouts.length - 1) ? <span className='f3'>·</span> : null}
            </React.Fragment>
        );
    });

    return (
        <div className='pt0 pb3'>
            <div className="flex items-center external-links-container">
                {linkItems}
            </div>
        </div>
    );
}
