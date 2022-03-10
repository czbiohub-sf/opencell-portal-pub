import React, { Component, useState } from 'react';

import 'tachyons';
import '../about/about.scss';


export default function Contact (props) {
    return (
        <div className='w-100 pt4 flex justify-center about-page-container'>
            <div className='w-70 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>Contact us</div>
                <div className='w-100 f5 pt3'>
                    <p>
                        OpenCell is a work in progress! We welcome comments, feedback, and bug reports.
                        We would also love to hear about how you are using our data. 
                        To share feedback, to suggest proteins you'd like to see us tag, 
                        or to express interest in our reagents, please reach out using the link below.                 
                    </p>

                    <div className='pt2 w-100 flex justify-center'>
                        <div className='w-50 pa2 pl5 pr5 tc b callout-container'>
                            <a target='_blank' href='https://docs.google.com/forms/d/e/1FAIpQLSeJbwuhViN4aFrQZnr-7i_W1JSm-Wq4KToieJVj5kZCk5VjEg/viewform'>
                                Reach out to us!
                            </a>
                        </div>
                    </div>

                    <p className='pt3'>
                        For technical questions or bug reports, please email us directly
                        at <a target='_blank' href='mailto:opencell@czbiohub.org'>opencell@czbiohub.org</a>. 
                    </p>
                    <p>
                        Follow us on Twitter <a target='_blank' href='https://twitter.com/opencellczb'>
                            @OpencellCZB
                        </a> for project updates!
                    </p>
                </div>
            </div>
        </div>
    );
};
