import { defineConfig } from "vite";
import path from "path";

export default defineConfig(({ mode }) => {
  const isDev = mode === "development";

  return {
    root: path.resolve(__dirname, "hr_core/static_src"),

    // Keep base as a URL path. Let templates decide dev-server URL vs built files.
    base: isDev ? "/" : "/static/hr_core/dist/",

    server: {
      strictPort: true,
      port: 5173,

      // host:true is fine if you want LAN access. If not, lock it down.
      host: "127.0.0.1",

      origin: "http://127.0.0.1:5173",

      // Helps when file watching is flaky (WSL/VMs/network FS)
      watch: {
        usePolling: true,
        interval: 100,
      },

      hmr: {
        host: "127.0.0.1",
        port: 5173,
      },
    },

    build: {
      manifest: true,
      outDir: path.resolve(__dirname, "hr_core/static/hr_core/dist"),
      emptyOutDir: true,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, "hr_core/static_src/js/main.js"),
        },
      },
    },
  };
});
