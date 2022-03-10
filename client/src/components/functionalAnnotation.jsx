import * as d3 from 'd3';
import React, { useState, useEffect } from 'react';
import settings from '../settings/settings.js';
import './functionalAnnotation.css';

export default function FunctionalAnnotation (props) {

    const [retrievedContent, setRetrievedContent] = useState();

    // retrieve the annotation if no content prop was provided
    useEffect(() => {
        if (!props.uniprotId) return;
        d3.json(`${settings.apiUrl}/uniprotkb_annotation/${props.uniprotId}`).then(data => {
            setRetrievedContent(data.functional_annotation);
        })
    }, [props.uniprotId]);

    const content = props.content || retrievedContent;
    return (
        <div className='pb2'>
            <div className='pt1 functional-annotation-container'>
                <p>{content ? content : 'No annotation available.'}</p>
            </div>
        </div>
    );
}
