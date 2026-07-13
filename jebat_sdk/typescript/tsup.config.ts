import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/hooks/index.ts'],
  format: ['esm', 'cjs'],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  treeshake: true,
  minify: false,
  platform: 'neutral',
  target: 'es2022',
  external: ['zod'],
  banner: {
    js: '// @nusabyte/jebat-sdk v1.0.0',
  },
  outDir: 'dist',
  tsconfig: 'tsconfig.json',
});