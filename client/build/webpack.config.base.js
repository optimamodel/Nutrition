const { VueLoaderPlugin } = require('vue-loader');
const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');


function resolve (dir) {
  return path.join(__dirname, '..', dir)
}

function root(){
  return path.join(__dirname, '..')
}

module.exports = {
  entry: [
    './src/index.js'
  ],
  output: {
		filename: "[name].[fullhash].js",
    publicPath: "",
		path: resolve('dist/'),
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
              options: {
              implementation: require('sass')
            }
          }
        ]
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
            plugins: ['@babel/plugin-transform-numeric-separator'],
            cacheDirectory: true,
          }
        }
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "src/index.html"
    }),
    new VueLoaderPlugin(),
    new CopyWebpackPlugin(
        {
          patterns: [
            {from: 'static/',
              to: resolve('dist/static/'),
              globOptions: {
                ignore: ['**/*.ai', '**/*.eps']
              }
            }
          ]
        }),
    new CleanWebpackPlugin()
  ]
}
