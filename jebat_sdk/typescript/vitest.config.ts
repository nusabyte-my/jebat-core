import { defineConfig } from 'vitest/config';
import tsconfigPaths from 'vitest-tsconfig-paths';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.spec.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['**/*.d.ts', '**/*.test.ts', '**/*.spec.ts', 'dist/**'],
    },
    isolate: true,
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: true,
      },
    },
  },
  plugins: [tsconfigPaths()],
});