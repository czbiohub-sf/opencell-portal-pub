
const path = require('path');
const webpack = require('webpack');
const {merge} = require('webpack-merge');
const commonConfig = require('./webpack.common.js');

const config = {

    mode: 'development',

    output: {
        path: path.resolve(__dirname, 'static'),
        filename: '[name].bundle.js',
        publicPath: '/',
    },

    devServer: {
        static: {
            directory: path.resolve(__dirname, 'static'),
        },

        port: 8080,
        
        // serve index.html in place of 404s to allow for client-side routing
        historyApiFallback: true,

        hot: false,
    },

    plugins: [
        new webpack.DefinePlugin({APP_MODE: JSON.stringify('private')}),
        new webpack.DefinePlugin({API_URL: JSON.stringify('http://localhost:5000')}),
        new webpack.DefinePlugin({GA_TRACKING_ID: JSON.stringify('UA-000000000-0')})
    ],

};

module.exports = merge(commonConfig, config);
