import * as d3 from 'd3';
import React, { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';

import ReactTable from 'react-table-6';
import { Callout } from '@blueprintjs/core';

import 'tachyons';
import 'react-table-6/react-table.css';
import "@blueprintjs/core/lib/css/blueprint.css";

import SectionHeader from '../../components/sectionHeader.jsx';
import * as popoverContents from '../../components/popoverContents.jsx';
import settings from '../../settings/settings.js';
import {renderConcentration, renderCopyNumber, ColumnHeaderWithPopover} from '../../settings/metadataDefinitions.js';
import SearchBar from '../../components/searchBar.jsx';


const columnDefs = [
    {
        id: 'ensg_id',
        accessor: row => row.ensg_id,
        Header: 'ENSG ID',
        width: 150,
    },{
        id: 'gene_name',
        accessor: row => row.gene_name,
        Header: 'Gene name',
        width: 120,
    },{
        id: 'protein_name',
        accessor: row => row.protein_name,
        Header: 'Protein name',
        width: 400,
    },{
        id: 'protein_copy_number',
        accessor: row => renderCopyNumber(
            602*(row.measured_abundance || row.imputed_abundance), 0
        ),
        Header: (
            <ColumnHeaderWithPopover 
                label={<span style={{fontSize: '14px'}}>Copy number<br></br>(per cell)</span>} 
                popover={popoverContents.proteinCopyNumber}
            />
        ),
        width: 125,
    },{
        id: 'protein_concentration',
        accessor: row => renderConcentration(
            row.measured_abundance || row.imputed_abundance, 0
        ),
        Header: (
            <ColumnHeaderWithPopover 
                label={<span style={{fontSize: '14px'}}>Concentration<br></br>(nM)</span>} 
                popover={popoverContents.proteinConcentration}
            />
        ),
        width: 125,
    },{
        id: 'status',
        accessor: row => row.status,
        Header: (
            <ColumnHeaderWithPopover
                label='Status'
                popover={popoverContents.searchResultsStatusColumn}
            />
        ),
        width: 120,
    },
];


export default function SearchResults (props) {
    
    const maxPageSize = 50;
    const history = useHistory();
    const [hits, setHits] = useState([]);
    const [loaded, setLoaded] = useState(false);

    // load the search results
    useEffect(() => {
        setLoaded(false);
        if (!props.match.params.query) {
            setHits([]);
            return;
        }
        d3.json(`${settings.apiUrl}/fsearch/${props.match.params.query}`).then(data => {
            setHits(data.hits || []);
            setLoaded(true);
        }, error => setLoaded(false));
    }, [props.match]);


    function getTrProps (state, rowInfo, column) {
        // onclick callback for react-table rows
        return {
            onClick: () => {
                if (rowInfo.original.published_cell_line_id) {
                    props.setCellLineId(rowInfo.original.published_cell_line_id);
                } else {
                    props.handleGeneNameSearch(rowInfo.original.gene_name);
                }
            }
        }
    }
    
    function getTheadThProps () {
        // vertically center the header labels in the react-table
        return {
            style: {
                display: 'flex', alignItems: 'center', justifyContent: 'center'
            }
        };
    }

    const noResultsFoundWarning = (
        <div className='pt3 w-70 flex flex-column justify-center'>
            <Callout
                intent='warning'
                title={`No results found for the search term "${props.match.params.query}"`}
            />
        </div>
    );

    const examples = (
        <div className='pt1 search-bar-hint'>
            {'For example: '}
            <Link to='/search/map4'>MAP4</Link>
            {', '}
            <Link to='/search/polr2'>POLR2</Link>
            {', '}
            <Link to='/search/chromatin'>chromatin</Link>
            {', '}
            <Link to='/search/mediator%20complex'>mediator complex</Link>
            {''}
        </div>
    );

    return (
        // note the hard-coded width here is tied to the sum of the column widths in columnDefs above
        
        <div className='pt3 pb3 pl5 ' style={{width: '1100px'}}>
            
            <div className='w-100 pb3'>
                <SectionHeader 
                    fontSize='f4'
                    title='Search for a protein'
                    popoverContent={popoverContents.searchResultsHeader}
                />
                <div className='w-50 pt2'>
                    <SearchBar
                        placeholder=' '
                        history={history}
                        handleGeneNameSearch={props.handleGeneNameSearch}
                    />
                </div>
                {examples}
            </div>

        {hits.length ? (
            <>
            <div className='pt1 b f5'>
                {`${hits.length} proteins found for the search term "${props.match.params.query}"`}
            </div>
            <div className='pt2'>
                <ReactTable
                    pageSize={Math.min(hits.length, maxPageSize)}
                    showPagination={hits.length > maxPageSize}
                    showPageSizeOptions={false}
                    filterable={false}
                    resizable={false}
                    columns={columnDefs}
                    data={hits}
                    getTrProps={getTrProps}
                    getTheadThProps={getTheadThProps}
                    getPaginationProps={() => ({style: {fontSize: 16}})}
                />
            </div>
            </>
        ) : null
        }

        {(loaded && props.match.params.query && !hits.length) ? noResultsFoundWarning : null}
        </div>
    );
}

