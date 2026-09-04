import { defineConfig } from 'vite';
import fs from 'fs';
import path from 'path';

export default defineConfig({
  base: './',
  build: {
    outDir: 'dist'
  },
  plugins: [
    {
      name: 'serve-public-html-directories',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url !== '/' && !req.url.includes('.')) {
            let cleanUrl = req.url.split('?')[0];
            if (!cleanUrl.endsWith('/')) {
              cleanUrl += '/';
            }
            const publicPath = path.join(__dirname, 'public', cleanUrl, 'index.html');
            if (fs.existsSync(publicPath)) {
              req.url = cleanUrl + 'index.html';
            }
          }
          next();
        });
      }
    }
  ]
});
