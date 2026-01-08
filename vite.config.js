// vite.config.js

import { defineConfig } from "vite";
import path from "path";

export default defineConfig(({ mode }) => {
  const isDev = mode !== "production";

console.log("[vite.config] mode=", mode, "isDev=", isDev, "root=", path.resolve(__dirname, "hr_core/static_src"));

  // Set this when using ngrok:
  // VITE_PUBLIC_HOST=shiniest-contritely-robbyn.ngrok-free.dev
  const publicHost = process.env.VITE_PUBLIC_HOST || "";

  const usingTunnel = isDev && !!publicHost;

  return {
    root: path.resolve(__dirname, "hr_core/static_src"),

    // Keep base as a URL path.
    base: isDev ? "/" : "/static/hr_core/dist/",

    server: {
      strictPort: true,
      port: 5173,

      // Vite can remain localhost-only because Caddy reverse-proxies to it.
      host: "127.0.0.1",

      // Don't force origin to 127.0.0.1 in tunnel mode; let Caddy/ngrok be the origin.
      origin: usingTunnel ? `https://${publicHost}` : "http://127.0.0.1:5173",

      watch: {
        usePolling: true,
        interval: 100,
      },

      hmr: usingTunnel
        ? {
            protocol: "wss",
            host: publicHost,
            clientPort: 443,
          }
        : {
            protocol: "ws",
            host: "127.0.0.1",
            port: 5173,
          },
    },

    build: {
      manifest: "manifest.json", // <- force it into dist/manifest.json
      outDir: path.resolve(__dirname, "hr_core/static/hr_core/dist"),
      emptyOutDir: true,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, "hr_core/static_src/js/main.js"),
        },
      },
    }

  };
});
