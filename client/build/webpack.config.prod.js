const { merge } = require('webpack-merge');
const base = require('./webpack.config.base.js');

module.exports = merge(base, {
  resolve: {
    alias: {
      vue: 'vue/dist/vue.min.js'
    }
  },
  mode: 'production',
  optimization: {
    splitChunks: {
      chunks: 'all'
    }
  }
})

