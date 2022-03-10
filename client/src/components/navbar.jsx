
import React, { useState, useEffect, useContext } from 'react';
import { Link, useHistory } from 'react-router-dom';

import SearchBar from './searchBar.jsx';
import settings from '../settings/settings.js';
import './navbar.scss';
import { Menu, Popover, Icon } from '@blueprintjs/core';


export default function Navbar (props) {

    const history = useHistory();
    const modeContext = useContext(settings.ModeContext);

    const exploreMenuItems = (
        <>
            <Menu.Item text="All tagged proteins" onClick={() => history.push('/targets')}/>
            <Menu.Item text="Microscopy gallery" onClick={() => history.push('/gallery')}/>
            <Menu.Item text="Search for a protein" onClick={() => history.push('/search')}/>
        </>
    );
    const helpMenuItems = (
        <>
            <Menu.Item text="Download data" onClick={() => history.push('/download')}/>
            <Menu.Item text="How-to guide" onClick={() => history.push('/help')}/>
            <Menu.Item text="About OpenCell" onClick={() => history.push('/about')}/>
            <Menu.Item text="Contact" onClick={() => history.push('/contact')}/>
        </>
    );
    const privateMenuItems = (
        <>
            <Menu.Divider/>
            <Menu.Item text="FOVs" onClick={() => history.push('/fovs')}/>
            <Menu.Item text="Annotations" onClick={() => history.push('/annotations')}/>
            <Menu.Item text="Public mode" onClick={() => window.location.search = '?mode=public'}/>
        </>
    );
    const exploreMenu = (
        <Menu>
            {exploreMenuItems}
            {modeContext==='private' ? privateMenuItems : null}
        </Menu>
    );
    const helpMenu = (
        <Menu>
            {helpMenuItems}
        </Menu>
    );

    return (
        // 'justify-between' here will left- and right-justify the two children divs
        <div className="flex items-center justify-between w-100 pr3 pl3 navbar-container">

            {/* the background image */}
            <div className="flex items-center">
                <div style={{flex: '1 1 100%', marginBottom: '-4px'}}>
                    <img 
                        width={null} 
                        height={45} 
                        style={{mixBlendMode: 'darken'}}
                        src='/assets/images/oc_banner_transparent.png' 
                    />
                </div>
            </div>

            {/* 'opencell' name (with dropdown menu) and search textbox */}
            <div className="flex items-center">

                <div className="pl3">
                    <span className='navbar-opencell-title'>
                        <Link to='/'>OpenCell</Link>
                    </span>
                </div>

                <Popover content={exploreMenu} modifiers={{arrow: {enabled: false}}}>
                    <div className='flex items-center'>
                        <div className="pl3 navbar-menu-header">
                            Explore
                        </div>
                        <div className='pl1 pt0'>
                            <Icon icon='caret-down' size={18} className='navbar-menu-icon'/>
                        </div>
                    </div>
                </Popover>

                <Popover content={helpMenu} modifiers={{arrow: {enabled: false}}}>
                    <div className='flex items-center'>
                        <div className="pl3 navbar-menu-header">
                            Help
                        </div>
                        <div className='pl1 pt0'>
                            <Icon icon='caret-down' size={18} className='navbar-menu-icon'/>
                        </div>
                    </div>
                </Popover>

                <div className='flex items-center pl3'>
                    <SearchBar 
                        handleGeneNameSearch={props.handleGeneNameSearch}
                        history={history}
                    />
                </div>
            </div>
        </div>
    );
}

