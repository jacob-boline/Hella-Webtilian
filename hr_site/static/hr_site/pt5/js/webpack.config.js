const path = require("path");

module.exports = {
    entry: "./hr_site/static/hr_site/pt5/js/webpack-entry.js",
    output: {
        filename: "bundle.js",
        path: path.resolve(__dirname),
    },
    mode: "development",
    module: {
        rules: [
            {
                test: /\.js$/, // Target JavaScript files
                exclude: /node_modules/, // Exclude node_modules for performance
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ["@babel/preset-env"],
                    },
                },
            },
        ],
    },
};

    // devServer: {
    //     //contentBase: path.resolve(__dirname, "dist"),
    //     static: path.resolve(__dirname, "static"),
    //     port: 3000,
    //     hot: true,
    //     open: true,
    //     //historyApiFallback: true,
    //     watchFiles: ["hr_site/static/hr_site/pt5/js/**/*"],
    // },

