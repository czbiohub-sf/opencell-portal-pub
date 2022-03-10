
import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';

import './footer.scss';


export default function Footer (props) {

    return (
        <div className='pt3'>
            <div className='footer-container flex justify-center items-center'>
                <span>{'© 2021-2022 The Chan Zuckerberg Biohub'}</span>
                <span><Link to='/privacy'>Privacy and cookie policy</Link></span>
                <span><Link to='/contact'>Contact us</Link></span>
            </div>
        </div>
    );
}
