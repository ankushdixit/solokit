import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        React: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
  {
    files: ["**/*.test.{js,jsx,ts,tsx}", "tests/**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.jest,
        NodeJS: "readonly",
      },
    },
  },
  {
    ignores: [
      // Dependencies
      "node_modules/**",
      // Build outputs
      ".next/**",
      "out/**",
      "dist/**",
      "build/**",
      // Reports and coverage
      "report/**",
      "reports/**",
      "coverage/**",
      ".stryker-tmp/**",
      // Test artifacts
      "playwright-report/**",
      "test-results/**",
      // Session data
      ".session/**",
      // Environment files (not JS, but good to exclude)
      ".env",
      ".env.local",
      ".env.*.local",
    ],
  },
];
