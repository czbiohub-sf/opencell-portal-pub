import React, { Component, useState  } from 'react';
import classNames from 'classnames';
import {Popover, Icon} from '@blueprintjs/core';

import './metadata.scss';


function MetadataItem (props) {

    let value = (
        <strong className={`f${props.smaller ? props.scale + 1 : props.scale}`}>
            {props.value || 'NA'}
        </strong>
    );
    value = props.url ? <a href={props.url} target='_blank'>{value}</a> : value;

    const popover = props.popoverContent ? (
        <Popover>
            <Icon icon='info-sign' iconSize={10} color="#bbb"/>
            {props.popoverContent}
        </Popover>
    ) : null;

    return (
        <div className={props.className}>
            {value}
            <abbr className={`f${props.scale + 1}`} title='units description'>
                {props.units}
                <span className='pl1'>{props.warning}</span>
            </abbr>

            <div className='flex items-center'>
                <div className={`pr1 f${props.scale + 2} metadata-item-label`}>{props.label}</div>
                {popover}
            </div>
        </div>
    );
}


function MetadataContainer (props) {

    if (!props.data) return null;

    const className = classNames(
        'metadata-item',
        {
            'pb2 flex-0-0': props.orientation==='row',
            'pt2': props.orientation==='column',
        }
    );

    const metadataItems = props.definitions.map(def => {
        return (
            <MetadataItem
                key={def.id}
                scale={props.scale}
                className={className}
                value={def.accessor(props.data)}
                label={def.Header}
                units={def.units}
            />
        );
    });

    return (
        <div
            className={`flex flex-wrap ${props.className}`} 
            style={{flexDirection: props.orientation}}
        >
            {metadataItems}
        </div>
    );
}


export {
    MetadataItem,
    MetadataContainer,
};