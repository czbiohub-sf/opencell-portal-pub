import * as d3 from 'd3';
import React, { Component } from 'react';

import chroma from 'chroma-js';
import ResponsiveXYFrame from "semiotic/lib/ResponsiveXYFrame";
import settings from '../settings/settings.js';

class ExpressionPlot extends Component {
    // A scatterplot of two measures of protein expression:
    // gene expresion from RNAseq and protein abundance from mass spec

    constructor (props) {

        super(props);

        // highlight the selected data point in blue
        this.backgroundDotColor = '#6663';
        this.selectedDotColor = '#00a1dd';
        this.selectedDotFillColor = chroma(this.selectedDotColor).alpha(.7);
        this.selectedDotStrokeColor = chroma(this.selectedDotColor).darken();

        const yExtent = [-2, 5];
        const xExtent = [0, 4];

        const axes = [
            {
                orient: 'left',
                label: 'Protein abundance (log10 nM)',
                tickValues: [-2, -1, 0, 1, 2, 3, 4, 5,],
                tickFormat: val => val.toFixed(0),
            },{
                orient: 'bottom',
                label: 'RNA abundance (log10 tpm)',
                tickValues: [0, 1, 2, 3, 4],
                tickFormat: val => val.toFixed(1),
            }
        ];

        // legend
        const foregroundGraphics = [(
            <text key={'active'} x={60} y={30} style={{fill: chroma(this.selectedDotColor)}}>
                <tspan fontSize="14">{'● Selected protein'}</tspan>
            </text>
        ),(
            <text key={'all'} x={60} y={50} style={{fill: '#777'}}>
                <tspan fontSize="14">{'● All proteins'}</tspan>
            </text>
        )];

        // hard-coded constant XYFrame props
        // note that the width here is ignored by ResponsiveXYFrame
        this.frameProps = {
            size: [400, 250],
            margin: {left: 50, bottom: 60, right: 10, top: 10},
            xExtent,
            yExtent,
            axes,
            xAccessor: 'rna_abundance',
            yAccessor: 'protein_abundance',
            foregroundGraphics,
        };

        this.state = {loaded: false};
        this.backgroundPoints = [];
        this.loadBackgroundData = this.loadBackgroundData.bind(this);
        this.moveAxisLabels = this.moveAxisLabels.bind(this);
    }

    componentDidMount () {
        this.loadBackgroundData();
        this.moveAxisLabels();
    }

    componentDidUpdate () {
        this.moveAxisLabels();
    }

    shouldComponentUpdate (prevProps) {
        return true;
    }

    loadBackgroundData () {
        d3.json(`${settings.apiUrl}/abundance`).then(data => {
            this.backgroundPoints = data.map(d => {
                return {
                    // gene expression from RNAseq (in tpm)
                    'rna_abundance': Math.log10(d.rna),
            
                    // protein abundance from mass spec (in nanomolar)
                    'protein_abundance': Math.log10(d.pro),

                    isBackground: true,
                };
            });
            this.setState({loaded: true});
        }, error => this.setState({loaded: true}));
    }

    moveAxisLabels () {
        // ugly hack to move the y-axis label a bit closer to the y-axis
        d3.select(this.node)
            .selectAll('.axis-title.y')
            .style('transform', 'translate(-30px, 90px) rotate(-90deg)');
    }

    render () {

        const selectedPoint = {
            isBackground: false,
            rna_abundance: Math.log10(this.props.rnaAbundance),
            protein_abundance: Math.log10(this.props.proteinAbundance),
        };

        let points =[...this.backgroundPoints];

        // this is a bit of a hack that relies on the fact that Math.log10(undefined) is NaN
        if (!isNaN(selectedPoint.rna_abundance)) {
            points = [...points, selectedPoint];
        }

        const pointStyle = (d, i) => {
            const isActive = !d.isBackground;
            return {
                r: isActive ? 5 : 2,
                fill: isActive ? this.selectedDotFillColor : this.backgroundDotColor,
                stroke: isActive ? this.selectedDotStrokeColor : null,
            };
        };

        return (
            <div ref={node => this.node = node}>
                <ResponsiveXYFrame
                    responsiveWidth={true}
                    points={points}
                    pointStyle={pointStyle}
                    {...this.frameProps}
                />
            </div>
        );
    }
}


export default ExpressionPlot;
