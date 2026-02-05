// vite.config.js

import path from "path";
import {defineConfig} from "vite";

export default defineConfig(({mode}) => {
    const isDev = mode !== "production";

    const webRoot = path.resolve(__dirname); // /home/app/web in the container
    const srcRoot = path.resolve(webRoot, "hr_core/static_src");
    const nodeModules = path.resolve(webRoot, "node_modules"); // where npm install puts deps

    const publicHost = process.env.VITE_PUBLIC_HOST || "";
    const usingTunnel = isDev && !!publicHost;

    const devHost = process.env.VITE_DEV_HOST || "127.0.0.1";  // aka local w/ docker || local w/out docker
    const hmrHost = process.env.VITE_HMR_HOST || (devHost === "0.0.0.0" ? "127.0.0.1" : devHost);
    const hmrClientPort = parseInt(process.env.VITE_HMR_CLIENT_PORT || '5173', 10); // typically should match devOrigin
    const devOrigin = process.env.VITE_DEV_ORIGIN || `http://${hmrHost}:${hmrClientPort}`;  // same as above, typically  (5174||5173)

    return {
        root: srcRoot,
        base: isDev ? "/" : "/static/hr_core/dist/",

        server: {
            strictPort: true,
            port: 5173,
            host: devHost,
            cors: true,
            fs: {
                allow: [
                    srcRoot,
                    nodeModules
                ]
            },
            origin: usingTunnel ? `https://${publicHost}` : devOrigin,

            watch: {usePolling: true, interval: 100},

            hmr: usingTunnel
                ? {protocol: "wss", host: publicHost, clientPort: 443}
                : {protocol: "ws", host: hmrHost, clientPort: hmrClientPort}
        },

        build: {
            manifest: "manifest.json",
            outDir: path.resolve(webRoot, "hr_core/static/hr_core/dist"),
            emptyOutDir: true,
            rollupOptions: {
                input: { main: path.resolve(srcRoot, "js/main.js") }
            }
        }
    };
});

