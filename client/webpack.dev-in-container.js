
const path = require('path');
const webpack = require('webpack');
const {merge} = require('webpack-merge');
const devConfig = require('./webpack.dev.js');

const config = {

    devServer: {
        // needed for webpack-dev-server running in a docker container
        host: '0.0.0.0',
        
        // use 9090 to distinguish from a non-containerized dev server
        port: 9090,
    },

    // needed for webpack-dev-server to detect changes when running in docker container
    // (ignore node_modules to prevent high CPU usage by the container)
    watchOptions: {
        poll: 3000,
        ignored: '**/node_modules',
    }
};

module.exports = merge(devConfig, config);
