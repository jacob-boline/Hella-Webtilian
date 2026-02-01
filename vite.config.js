// vite.config.js

import path from "path";
import {defineConfig} from "vite";

export default defineConfig(({ mode }) => {
  const isDev = mode !== "production";

  const publicHost = process.env.VITE_PUBLIC_HOST || "";
  const usingTunnel = isDev && !!publicHost;

  const devHost = process.env.VITE_DEV_HOST || "127.0.0.1";
  const devOrigin = process.env.VITE_DEV_ORIGIN || `http://${devHost}:5173`;
  const hmrHost = devHost === "0.0.0.0" ? "localhost" : devHost;

  return {
    root: path.resolve(__dirname, "hr_core/static_src"),
    base: isDev ? "/" : "/static/hr_core/dist/",

    server: {
      strictPort: true,
      port: 5173,
      host: devHost,
      origin: usingTunnel ? `https://${publicHost}` : devOrigin,

      watch: { usePolling: true, interval: 100 },

      hmr: usingTunnel
        ? { protocol: "wss", host: publicHost, clientPort: 443 }
        : { protocol: "ws", host: hmrHost, port: 5173 },
    },

    build: {
      manifest: "manifest.json",
      outDir: path.resolve(__dirname, "hr_core/static/hr_core/dist"),
      emptyOutDir: true,
      rollupOptions: {
        input: { main: path.resolve(__dirname, "hr_core/static_src/js/main.js") },
      },
    },
  };
});

