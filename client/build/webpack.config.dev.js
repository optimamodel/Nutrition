const { merge } = require('webpack-merge');
const base = require('./webpack.config.base.js');

module.exports = merge(base, {
  resolve: {
    alias: {
      vue: 'vue/dist/vue.js'
    }
  },
  mode: 'development',
  devtool: "eval-source-map",
})

