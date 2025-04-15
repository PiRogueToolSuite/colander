const CopyPlugin = require("copy-webpack-plugin");
const { VueLoaderPlugin } = require("vue-loader");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const path = require('path');

const jsDest = path.resolve(__dirname, './colander/static/js');
const cssDest = path.resolve(__dirname, './colander/static/css');
const jsLibDest = path.resolve(jsDest, 'externals');
const cssLibDest = path.resolve(cssDest, 'externals');
const componentsDest = path.resolve(jsDest, 'components');

let webpackConfig = (isDev, isProd) => [
  {
    devtool: 'source-map',
    entry: {
      'colander-widgets': path.resolve(__dirname, 'colander/frontend/colander-widgets/index.js'),
    },
    output: {
      filename: '[name].js',  // output bundle file name
      chunkFilename: 'async-[name].js',
      path: jsDest,  // path to our Django static directory
    },
    externals: {
      vue: 'Vue',
      jquery: 'jQuery',
    },
    plugins: [
      new CopyPlugin({
        patterns: [
          {
            from: isProd ? 'node_modules/jquery/dist/jquery.min.js'
                         : 'node_modules/jquery/dist/jquery.js',
            to: path.resolve(jsLibDest, 'jquery.min.js'),
          },
          {
            from: isProd ? 'node_modules/vue/dist/vue.global.prod.js'
                         : 'node_modules/vue/dist/vue.global.js',
            to: path.resolve(jsLibDest, 'vue.min.js'),
          },
          {
            from:  isProd ? 'node_modules/@popperjs/core/dist/umd/popper.min.js'
                          : 'node_modules/@popperjs/core/dist/umd/popper.js',
            to: path.resolve(jsLibDest, 'popper.min.js'),
          },
          {
            from:  isProd ? 'node_modules/bootstrap/dist/js/bootstrap.min.js'
                          : 'node_modules/bootstrap/dist/js/bootstrap.js',
            to: path.resolve(jsLibDest, 'bootstrap.min.js'),
          },
          {
            from:  isProd ? 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js'
                          : 'node_modules/bootstrap/dist/js/bootstrap.bundle.js',
            to: path.resolve(jsLibDest, 'bootstrap.bundle.min.js'),
          },
          {
            from: isProd ? 'node_modules/simplemde/dist/simplemde.min.js'
                         : 'node_modules/simplemde/debug/simplemde.js',
            to: path.resolve(jsLibDest, 'simplemde.min.js'),
          },
          {
            from: isProd ? 'node_modules/simplemde/dist/simplemde.min.css'
                         : 'node_modules/simplemde/debug/simplemde.css',
            to: path.resolve(cssLibDest, 'simplemde.min.css'),
          },
        ],
      }),
      new VueLoaderPlugin(),
      /*
      new MiniCssExtractPlugin({
        filename: '[name].css',
      }),
       */
    ],
    module: {
      rules: [
        {
          test: /\.vue$/,
          loader: 'vue-loader',
        },
        {
          test: /\.scss$/,
          use: [
            'vue-style-loader',
            'css-loader',
            'sass-loader',
          ],
        },
        {
          test: /\.css$/i,
          use: [/*MiniCssExtractPlugin.loader,*/ "css-loader"],
        },
      ]
    },
  },
  // Styles rules
  {
    devtool: 'source-map',
    entry: {
      'project': path.resolve(__dirname, 'colander/frontend/scss/project.scss'),
      'graph': path.resolve(__dirname, 'colander/frontend/scss/graph.scss'),
    },
    output: {
      filename: '.js-intermediate.[name].css-bundle.js',  // output bundle file name
      path: cssDest,                                      // path to our Django static directory
    },
    plugins: [
      new MiniCssExtractPlugin({
        filename: '[name].css',
      }),
    ],
    module: {
      rules: [
        {
          test: /\.scss$/,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            {
              loader: "sass-loader",
              options: {
                sassOptions: {
                  quietDeps: true,
                },
              },
            },
          ],
        },
      ],
    },
  },
];

module.exports = (env, argv) => {
  if (argv.mode === 'development') {

  }
  if (argv.mode === 'production') {

  }
  return webpackConfig(argv.mode === 'development', argv.mode === 'production');
};
