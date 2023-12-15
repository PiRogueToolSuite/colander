const path = require('path');

module.exports = [
  {
    entry: {
      'colander-dgraph': path.resolve(__dirname, 'colander/frontend/colander-dgraph/index.js'),
      'colander-widgets': path.resolve(__dirname, 'colander/frontend/colander-widgets/index.js'),
    },
    output: {
      filename: '[name].js',  // output bundle file name
      path: path.resolve(__dirname, './colander/static/js'),  // path to our Django static directory
    },
  }
];
