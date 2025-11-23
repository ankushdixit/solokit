#!/bin/bash
# Lighthouse CI wrapper script
# Auto-detects Chrome/Chromium location for cross-platform compatibility
# - GitHub Actions: Uses pre-installed Chrome
# - Local/VM: Uses Playwright's Chromium if Chrome not found

# Check if CHROME_PATH is already set
if [ -n "$CHROME_PATH" ] && [ -x "$CHROME_PATH" ]; then
  exec npx lhci autorun
fi

# Try common Chrome locations
CHROME_CANDIDATES=(
  "/usr/bin/google-chrome-stable"
  "/usr/bin/google-chrome"
  "/usr/bin/chromium-browser"
  "/usr/bin/chromium"
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

for candidate in "${CHROME_CANDIDATES[@]}"; do
  if [ -x "$candidate" ]; then
    export CHROME_PATH="$candidate"
    exec npx lhci autorun
  fi
done

# Fallback: Try to find Playwright's Chromium (be specific to avoid matching Firefox)
# Linux: ~/.cache/ms-playwright/chromium-XXXX/chrome-linux/chrome
PLAYWRIGHT_CHROME=$(find ~/.cache/ms-playwright -path "*/chromium-*/chrome-linux/chrome" -type f 2>/dev/null | head -1)

# macOS: ~/.cache/ms-playwright/chromium-XXXX/chrome-mac/Chromium.app/Contents/MacOS/Chromium
if [ -z "$PLAYWRIGHT_CHROME" ]; then
  PLAYWRIGHT_CHROME=$(find ~/.cache/ms-playwright -path "*/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium" -type f 2>/dev/null | head -1)
fi

if [ -n "$PLAYWRIGHT_CHROME" ] && [ -x "$PLAYWRIGHT_CHROME" ]; then
  export CHROME_PATH="$PLAYWRIGHT_CHROME"
  exec npx lhci autorun
fi

# No Chrome found - let lhci fail with helpful message
echo "Warning: Chrome/Chromium not found. Lighthouse CI may fail."
echo "Install Chrome or run 'npx playwright install chromium' first."
exec npx lhci autorun
