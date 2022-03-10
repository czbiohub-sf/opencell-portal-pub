import React, { Component, useState } from 'react';

import 'tachyons';
import '../about/about.scss';


export default function Privacy (props) {
    return (
        <div className='w-100 pt4 flex justify-center about-page-container'>
            <div className='w-70 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>OpenCell privacy and cookie policy</div>
                <div className='w-100 pt3 f5'>
                    <p>
                    We use cookies to enable the use of Google Analytics tools.
                    These tools allow us to understand how people use this website:
                    number of users, which pages are most often visited, etc.
                    This information is useful feedback to improve our user interface.
                    We do not link IP addresses to anything personally identifiable.
                    This means that user sessions will be tracked, but the users will remain anonymous.
                    At no time do we disclose site usage by individual IP addresses.
                    </p>
                    <p>
                        Learn more about Google Analytics <a href='https://developers.google.com/analytics/devguides/collection/analyticsjs/cookie-usage' target='_blank'>
                            here
                        </a>.
                    </p>
                    <p>
                    You are free to remove these cookies at any time by deleting them in your browser as applicable.
                    Please click <a href='https://aboutcookies.org' target='_blank'>here</a> to learn more about cookies,
                    including how to control, disable, or delete them.
                    </p>
                </div>
            </div>
        </div>
    );
};
