const path = require('path');

module.exports = {
  entry: './static/hr_site/index.js', // Adjust this path based on where your JS file is located
  output: {
    filename: 'js/bundle.js',
    path: path.resolve(__dirname, 'static/hr_site'),
  },
  module: {
  rules: [
    // Handle CSS files
    {
      test: /\.css$/,  // Match .css files
      use: ['style-loader', 'css-loader', 'postcss-loader'],
    },
    // Handle Font files (woff, woff2, ttf, otf, eot, svg)
    {
      test: /\.(woff|woff2|ttf|otf|eot|svg)$/,  // Match font files
      use: {
        loader: 'file-loader',
        options: {
          name: 'fonts/[name].[hash].[ext]',  // Font files output to the "fonts" folder with a hashed name
          outputPath: 'static/hr_site/fonts/',  // Output path for fonts
          publicPath: '/static/hr_site/fonts/',  // URL for accessing fonts in the browser
        },
      },
    },
    // Handle Image files (jpg, jpeg, png, gif, svg)
    {
      test: /\.(jpg|jpeg|png|gif|svg)$/,  // Match image files
      use: [
        {
          loader: 'file-loader',
          options: {
            name: '[name].[hash].[ext]',  // Save images with a hashed name
            outputPath: 'images/',  // Output to the "images" folder
            publicPath: '/static/hr_site/images/',  // Public path for accessing images in the browser
          },
        },
      ],
    },
  ],
},

  resolve: {
    extensions: ['.js', '.jsx', '.css'],
  },
  mode: 'production',
};
