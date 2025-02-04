const CopyPlugin = require("copy-webpack-plugin");

const path = require('path');

const jsDest = path.resolve(__dirname, './colander/static/js');
const jsLibDest = path.resolve(jsDest, 'externals');

let webpackConfig = (isDev, isProd) => [
  {
    entry: {
      'colander-dgraph': path.resolve(__dirname, 'colander/frontend/colander-dgraph/index.js'),
      'colander-widgets': path.resolve(__dirname, 'colander/frontend/colander-widgets/index.js'),
      'colander-text-editor': path.resolve(__dirname, 'colander/frontend/colander-text-editor/index.js'),
    },
    output: {
      filename: '[name].js',  // output bundle file name
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
            from: isProd ? 'node_modules/vue/dist/vue.global.prod.js' : 'node_modules/vue/dist/vue.global.js',
            to: path.resolve(jsLibDest, 'vue.min.js'),
          },
          {
            from: isProd ? 'node_modules/jquery/dist/jquery.min.js' : 'node_modules/jquery/dist/jquery.js',
            to: path.resolve(jsLibDest, 'jquery.min.js'),
          },
        ],
      })
    ]
  }
];

module.exports = (env, argv) => {
  if (argv.mode === 'development') {

  }
  if (argv.mode === 'production') {

  }
  return webpackConfig(argv.mode === 'development', argv.mode === 'production');
};
