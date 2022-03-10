import React, { Component, useState } from 'react';

import 'tachyons';
import '../about/about.scss';
import Callout from '../../components/callout.jsx';


export default function Jobs (props) {
    return (
        <div className='w-100 pt4 flex justify-center about-page-container'>
            <div className='w-70 pl5 pr5'>
                <div className='w-100 f3 bb b--black-30'>We're hiring!</div>
                <div className='w-100 f5 pt3'>
                    <p>
                        The Leonetti group at the Chan Zuckerberg Biohub is hiring for several roles 
                        to help push the OpenCell project in new and exciting directions. 
                        If you're interested in systems cell biology, genome engineering,
                        or high-throughput microscopy, check out the jobs below and apply!
                    </p>
                    <ul style={{lineHeight: 2}}>
                        <li>
                            <a target='_blank' href='https://apply.workable.com/czbiohub/j/BCD643A8E1/'>
                            Imaging Data Scientist - Computer Vision and High-throughput Microscopy
                            </a>
                        </li>
                        <li>
                            <a target='_blank' href='https://apply.workable.com/czbiohub/j/6C3DF6632B/'>
                            Senior Research Associate - Cell Biology and Genome Engineering
                            </a>
                        </li>
                        <li>
                            <a target='_blank' href='https://apply.workable.com/czbiohub/j/15A8CEF638/'>
                            Research Associate - Cell Biology and High-Throughput Screening
                            </a>
                        </li>
                        <li>
                            <a target='_blank' href='https://apply.workable.com/czbiohub/j/7432625A74/'>
                            Data Scientist - Mass Spectrometry and Computational Biology
                            </a>
                        </li>
                        <li>
                            <a target='_blank' href='https://apply.workable.com/czbiohub/j/E6BBD57AB2/'>
                            Scientist - Mass Spectrometry and Infectious Diseases
                            </a>
                        </li>
                    </ul>

                    <Callout hideIcon>
                        If you are interested in joining the team but these positions are not the right fit,
                        or if you are interested in doing a postdoc in the Leonetti group, 
                        please <a href='mailto:manuel.leonetti@czbiohub.org '>
                            <b>reach out to us directly</b>
                        </a>!
                    </Callout>

                </div>
            </div>
        </div>
    );
};

