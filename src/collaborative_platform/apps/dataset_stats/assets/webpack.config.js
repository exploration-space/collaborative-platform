const path = require('path');

const outputDirectory = '../static/dataset_stats/js'


module.exports = {
  entry: './src/index.js',
  output: {
    path: path.join(__dirname,outputDirectory)
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader"
        }
      },
      { test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        use: 'url-loader',
        test: /\.(png|jpg|svg)$/
      }
    ]
  },
  devServer: {
    port: 3000,
  },
  devtool: "cheap-module-source-map",
};