import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    // The Decision Twin API runs separately (uvicorn api.prediction_api:app).
    // Proxying /v1 and /v2 in dev keeps the browser on one origin, so there is
    // no CORS preflight in development that production would not also have.
    proxy: {
      "/v1": { target: "http://127.0.0.1:8078", changeOrigin: true },
      "/v2": { target: "http://127.0.0.1:8078", changeOrigin: true },
    },
  },
});
