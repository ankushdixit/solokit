import type { Config } from "tailwindcss";

/**
 * Tailwind CSS v4 Configuration
 *
 * In Tailwind v4, most configuration is done in CSS via @theme blocks.
 * This file is only needed for:
 * - Plugins
 * - Content paths (if automatic detection doesn't work)
 *
 * Theme customization (colors, spacing, radius) is done in globals.css
 * using the @theme directive for shadcn/ui compatibility.
 *
 * @see https://tailwindcss.com/docs/upgrade-guide
 */
const config: Config = {
  plugins: [],
};

export default config;
