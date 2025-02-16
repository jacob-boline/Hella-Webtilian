//
// const path = require('path');
// const BundleTracker = require('webpack-bundle-tracker');
//
//
// module.exports = {
//     mode: 'development',
//     entry: './hr_site/static/hr_site/pt3/pt3.js', // Your main JS file
//     output: {
//         filename: 'bundle.js',
//         path: path.resolve(__dirname, 'static/dist'),
//         publicPath: '/static/', // Ensure this matches Django's STATIC_URL
//     },
//     module: {
//         rules: [
//             {
//                 test: /\.css$/,
//                 use: ['style-loader', 'css-loader'], // Load and inject CSS
//             },
//         ],
//     },
//     devServer: {
//         static: {
//             directory: path.join(__dirname, 'static'),
//         },
//         port: 3000, // Choose an available port
//         hot: true, // Enable hot reloading
//         headers: {
//             'Access-Control-Allow-Origin': '*', // Allow cross-origin requests for Django
//         },
//     },
//     plugins: [
//         new BundleTracker({ path: __dirname, filename: 'webpack-stats.json' }),
//     ],
// };