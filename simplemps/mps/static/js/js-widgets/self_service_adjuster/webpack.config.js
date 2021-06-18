const _require = id => require(require.resolve(id, { paths: [require.main.path] }));
const HtmlWebpackPlugin = _require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const path = require('path');

module.exports = {
    entry: ['./src/index.js'],
    output: {
        // path: path.resolve(__dirname, './build'),
        path: path.join(__dirname,'..','..','/rep','/proposal','/js','/compiled','/adjuster'),
        filename: 'bundle.js'
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: "./static/index.html",
            filename: "index.html"
        }),
        new MiniCssExtractPlugin()
    ],
    resolve: {
        extensions: [".js",".jsx"]
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader"
                }
            },
            {
                test: /\.(js|jsx)$/,
                use: ["source-map-loader"],
                enforce: "pre"
            },
            {
                test: /\.(css)$/i,
                use: ['css-loader']
            },
            {
                test: /\.(png|jpe?g|gif|woff|ttf|svg|eot|env)$/i,
                use: [
                  {
                    loader: 'file-loader',
                  },
                ],
            },
        ]
    },
    stats: 'errors-only'
};