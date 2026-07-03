import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm', 'cjs'],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  external: ['ws'],
  noExternal: ['zod'],
  treeshake: true,
  minify: false,
  platform: 'node',
  target: 'node18',
  outDir: 'dist',
});