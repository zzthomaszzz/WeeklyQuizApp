import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './test/setup',
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html', 'lcov'],
            reportsDirectory: './coverage',
            include: ['src/**/*.{ts,tsx}'],
            exclude: [
                'src/**/*.test.{ts,tsx}',
                'src/main.tsx',
                'src/test/**',
                'src/types/**',
            ],
            // Thresholds sit at the level the suite currently reaches.
            // Raise them as coverage improves; never lower them to pass.
            thresholds: {
                statements: 70,
                branches: 70,
                functions: 70,
                lines: 70,
            },
        },
    },
})
