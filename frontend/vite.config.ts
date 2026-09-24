import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 后端同时挂载 /api/... 路由，与生产 Nginx 的 proxy_pass 行为保持一致，不做路径重写
      "/api": {
        target: "http://localhost:29519",
        changeOrigin: true,
      },
    },
  },
});
