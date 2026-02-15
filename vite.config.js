// vite.config.js

import path from "path";
import {defineConfig} from "vite";

export default defineConfig(({mode}) => {
    const isDev = mode !== "production";

    const webRoot = path.resolve(__dirname); // /home/app/web in the container
    const srcRoot = path.resolve(webRoot, "hr_core/static_src");
    const staticRoot  = path.resolve(webRoot, "hr_core/static");   // 👈 ADD THIS
    const nodeModules = path.resolve(webRoot, "node_modules"); // where npm install puts deps

    // Tunnel support (optional)
    const publicHost = process.env.VITE_PUBLIC_HOST || "";
    const usingTunnel = isDev && !!publicHost;

    // Dev server binding + HMR config
    const devHost = process.env.VITE_DEV_HOST || "127.0.0.1"; // local w/ docker || local w/out docker
    const hmrHost = process.env.VITE_HMR_HOST || (devHost === "0.0.0.0" ? "127.0.0.1" : devHost);
    const hmrClientPort = parseInt(process.env.VITE_HMR_CLIENT_PORT || "5173", 10);
    const devOrigin = process.env.VITE_DEV_ORIGIN || `http://${hmrHost}:${hmrClientPort}`;

    // When the page is served by Django/Nginx (e.g. :8080) but CSS/JS come from Vite (:5173),
    // any CSS url("/static/...") requests will hit Vite. Proxy them back to the app server.
    // Override VITE_BACKEND_ORIGIN if your backend isn't reachable at localhost from the Vite process/container.
    const backendOrigin = process.env.VITE_BACKEND_ORIGIN || "http://localhost:8080";

    return {
        root: srcRoot,
        base: isDev ? "/" : "/static/hr_core/dist/",

        server: {
            strictPort: true,
            port: 5173,
            host: devHost,
            cors: true,
            fs: {
                allow: [srcRoot, staticRoot, nodeModules]
            },

            origin: usingTunnel ? `https://${publicHost}` : devOrigin,

            // Dev-only proxy so /static (and /media) work when assets are referenced from Vite-served CSS/JS.
            proxy: isDev
                ? {
                    "/static": {
                        target: backendOrigin,
                        changeOrigin: true,
                    },
                    "/media": {
                        target: backendOrigin,
                        changeOrigin: true,
                    },
                }
                : undefined,

            watch: {usePolling: true, interval: 100},

            hmr: usingTunnel
                ? {protocol: "wss", host: publicHost, clientPort: 443}
                : {protocol: "ws", host: hmrHost, clientPort: hmrClientPort},
        },

        build: {
            manifest: "manifest.json",
            outDir: path.resolve(webRoot, "hr_core/static/hr_core/dist"),
            emptyOutDir: true,
            rollupOptions: {
                input: {
                    main: path.resolve(srcRoot, "js/main.js"),
                    critical: path.resolve(srcRoot, "css/critical.css"),
                    noncritical: path.resolve(srcRoot, "css/noncritical.css"),
                },
            },
        },
    };
});
