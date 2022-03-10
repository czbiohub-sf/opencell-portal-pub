import * as d3 from 'd3';
import React, { useState, useEffect, useContext } from 'react';
import ReactTable from 'react-table-6';

import SectionHeader from './sectionHeader.jsx';
import * as popoverContents from './popoverContents.jsx';
import settings from '../settings/settings.js';
import { 
    cellLineMetadataDefinitions, 
    renderConcentration, 
    renderCopyNumber, 
    ColumnHeaderWithPopover
} from '../settings/metadataDefinitions.js';

import 'tachyons';
import 'react-table-6/react-table.css';


// column defs for the cell line table in 'public' mode
// HACK: these are partial copies of the column defs in metadataDefinitions and in searchResults
const publicColumnDefs = [
    {
        id: 'ensg_id',
        accessor: row => row.metadata?.ensg_id,
        Header: 'ENSG ID',
        width: 150,
    },{
        id: 'gene_name',
        Header: 'Gene name',
        accessor: row => row.metadata?.target_name,
        width: 100,
    },{
        id: 'target_terminus',
        accessor: row => row.metadata?.target_terminus,
        Header: <>Tag<br></br>terminus</>,
        width: 80,
    },{
        id: 'protein_name',
        accessor: row => row.uniprot_metadata?.protein_name,
        Header: 'Protein name',
        width: 350,
    },{
        id: 'protein_concentration',
        accessor: row => renderConcentration(row?.abundance_data?.protein_concentration),
        Header: (
            <ColumnHeaderWithPopover 
                label={<span style={{fontSize: '14px'}}>Concentration<br></br>(nM)</span>} 
                popover={popoverContents.proteinConcentration}
            />
        ),
        width: 125,
    },{
        id: 'protein_copy_number',
        accessor: row => renderCopyNumber(row?.abundance_data?.protein_copy_number),
        Header: (
            <ColumnHeaderWithPopover 
                label={<span style={{fontSize: '14px'}}>Copy number<br></br>(per cell)</span>} 
                popover={popoverContents.proteinCopyNumber}
            />
        ),
        width: 125,
    },
]


export default function CellLineTable (props) {

    const modeContext = useContext(settings.ModeContext);
    const [allCellLines, setAllCellLines] = useState([]);

    // load the metadata for all cell lines
    useEffect(() => {
        const url = `${settings.apiUrl}/lines?publication_ready=${modeContext==='public'}`;
        d3.json(url).then(lines => {
            // sort targets alphabetically by default
            lines = lines.sort((a, b) => a.metadata.target_name > b.metadata.target_name ? 1 : -1);
            setAllCellLines(lines);
        });
    }, [])
    
    const hiddenColumnDefIds = ['facs_intensity', 'facs_area', ];
    let columnDefs = cellLineMetadataDefinitions.filter(
        def => !hiddenColumnDefIds.includes(def.id)
    );
    
    // use hard-coded column defs in public mode
    if (modeContext==='public') columnDefs = publicColumnDefs;

    return (
        <>
        {/* table of all targets */}
        <div className='pl5 pr5 pt3 pb2 w-100'>
            <SectionHeader
                fontSize='f4'
                title='All OpenCell targets'
                popoverContent={popoverContents.cellLineTableHeader}
            />

            <div className='pt3' style={{width: '950px'}}>
                <ReactTable 
                    defaultPageSize={25}
                    showPageSizeOptions={true}
                    filterable={true}
                    resizable={modeContext!=='public'}
                    columns={columnDefs}
                    data={allCellLines}
                    getTrProps={(state, rowInfo, column) => {
                        const isActive = rowInfo && rowInfo.original.metadata.cell_line_id===props.cellLineId;
                        return {
                            onClick: () => props.setCellLineId(rowInfo.original.metadata.cell_line_id),
                            style: {
                                background: isActive ? '#ddd' : null,
                                fontWeight: isActive ? 'bold' : 'normal'
                            }
                        }
                    }}
                    getPaginationProps={(state, rowInfo, column) => {
                        return {style: {fontSize: 16}}
                    }}
                    defaultFilterMethod={(filter, row, column) => {
                        // force default filtering to be case-insensitive
                        const id = filter.pivotId || filter.id;
                        const value = filter.value.toLowerCase();
                        return row[id] !== undefined ? String(row[id]).toLowerCase().startsWith(value) : true
                    }}
                    getTheadThProps={() => {
                        // vertically center the header labels
                        return {
                            style: {
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }
                        };
                    }}
    
                />
            </div>
        </div>
        {allCellLines.length ? (null) : (<div className='f2 tc loading-overlay'>Loading...</div>)}
    </>
    );
}