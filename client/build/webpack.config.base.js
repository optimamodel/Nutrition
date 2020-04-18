const { VueLoaderPlugin } = require('vue-loader');
const webpack = require('webpack');
const path = require('path');

function resolve (dir) {
  return path.join(__dirname, '..', dir)
}

function root(){
  return path.join(__dirname, '..')
}

module.exports = {
  resolve: {
    alias: {
      vue: 'vue/dist/vue.js'
    }
  },
  devServer: {
    hot: true,
    watchOptions: {
      poll: true
    }
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        use: 'vue-loader'
      },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          {
            loader: "style-loader"
          },
          {
            loader: "css-loader",
          },
          {
            loader: "sass-loader",
          }
        ]
      },
      {
        test: /\.js$/,
        use: 'babel-loader'
      }
    ]
  },
}
