import { defineConfig } from 'vite';
export default defineConfig({build:{outDir:'../backend/static',emptyOutDir:false,lib:{entry:'src/main.ts',formats:['es'],fileName:()=> 'atlas.js'},rollupOptions:{output:{assetFileNames:'[name][extname]'}}}});
