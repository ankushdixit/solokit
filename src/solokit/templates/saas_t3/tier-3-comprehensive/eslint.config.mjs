import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import globals from "globals";
import jestDomPlugin from "eslint-plugin-jest-dom";
import testingLibraryPlugin from "eslint-plugin-testing-library";

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
      // Complexity rules (tier-3)
      complexity: ["error", { max: 10 }],
      "max-depth": ["error", { max: 4 }],
      "max-nested-callbacks": ["error", { max: 4 }],
      "max-lines-per-function": [
        "warn",
        {
          max: 100,
          skipBlankLines: true,
          skipComments: true,
        },
      ],
    },
  },
  {
    files: [
      "**/*.test.{js,jsx,ts,tsx}",
      "tests/unit/**/*.{js,jsx,ts,tsx}",
      "tests/integration/**/*.{js,jsx,ts,tsx}",
      "tests/setup.{js,jsx,ts,tsx}",
      "jest.setup.{js,jsx,ts,tsx}",
    ],
    languageOptions: {
      globals: {
        ...globals.jest,
        NodeJS: "readonly",
      },
    },
    plugins: {
      "jest-dom": jestDomPlugin,
      "testing-library": testingLibraryPlugin,
    },
    rules: {
      // jest-dom rules
      "jest-dom/prefer-checked": "error",
      "jest-dom/prefer-enabled-disabled": "error",
      "jest-dom/prefer-required": "error",
      "jest-dom/prefer-to-have-attribute": "error",
      // testing-library rules
      "testing-library/await-async-queries": "error",
      "testing-library/no-await-sync-queries": "error",
      "testing-library/no-debugging-utils": "warn",
      "testing-library/prefer-screen-queries": "error",
      // Disable complexity rules for test files
      "max-nested-callbacks": "off",
      "max-lines-per-function": "off",
    },
  },
  {
    files: ["tests/e2e/**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.node,
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
      // Environment files
      ".env",
      ".env.local",
      ".env.*.local",
    ],
  },
];
