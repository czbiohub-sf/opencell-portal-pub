import React from 'react';
import { Icon } from "@blueprintjs/core";
import './callout.scss';


export default function Callout (props) {
    return (
        <div className='w-100 pa2 mt3 callout-container'>
            <div className='f5 flex items-center'>
                {props.hideIcon ? null : <Icon icon='info-sign' iconSize={16}/>}
                <div className='pl2'>
                    {props.children}
                </div>
            </div>
        </div>
    );
}