# Solokit Badge

Add a "Built with solokit" badge to your projects. The badge automatically handles dark/light mode based on system preference.

## Quick Start

Add these two lines to your project:

```html
<script src="https://getsolokit.com/badge.js" defer></script>
<div id="solokit-badge"></div>
```

## Options

| Attribute | Values | Default | Description |
|-----------|--------|---------|-------------|
| `data-theme` | `auto`, `light`, `dark` | `auto` | Force theme or auto-detect |
| `data-position` | `inline`, `fixed` | `inline` | Inline or fixed bottom-right corner |

### Examples

```html
<!-- Fixed position (bottom-right corner) -->
<div id="solokit-badge" data-position="fixed"></div>

<!-- Force dark theme -->
<div id="solokit-badge" data-theme="dark"></div>

<!-- Multiple badges (use class instead of id) -->
<div class="solokit-badge"></div>
<div class="solokit-badge"></div>
```

## Framework Examples

### React / Next.js

```tsx
"use client";

import Script from "next/script";

export function SolokitBadge() {
  return (
    <>
      <Script src="https://getsolokit.com/badge.js" strategy="lazyOnload" />
      <div id="solokit-badge" />
    </>
  );
}
```

Usage:
```tsx
import { SolokitBadge } from "@/components/SolokitBadge";

export default function Page() {
  return (
    <main>
      {/* Your content */}
      <footer>
        <SolokitBadge />
      </footer>
    </main>
  );
}
```

### Vue

```vue
<template>
  <div id="solokit-badge"></div>
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  const script = document.createElement('script');
  script.src = 'https://getsolokit.com/badge.js';
  document.body.appendChild(script);
});
</script>
```

### Svelte

```svelte
<script>
  import { onMount } from 'svelte';

  onMount(() => {
    const script = document.createElement('script');
    script.src = 'https://getsolokit.com/badge.js';
    document.body.appendChild(script);
  });
</script>

<div id="solokit-badge"></div>
```

### Streamlit (Python)

```python
import streamlit as st
from streamlit.components.v1 import html

def solokit_badge(theme="auto", position="inline"):
    html(f"""
        <script src="https://getsolokit.com/badge.js" defer></script>
        <div id="solokit-badge" data-theme="{theme}" data-position="{position}"></div>
    """, height=40)

# Usage - add at the bottom of your app
st.title("My App")
# ... your app content ...

st.divider()
solokit_badge()
```

### Flask / Jinja2

In your base template:

```html
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}{% endblock %}</title>
</head>
<body>
  {% block content %}{% endblock %}

  <footer>
    <script src="https://getsolokit.com/badge.js" defer></script>
    <div id="solokit-badge"></div>
  </footer>
</body>
</html>
```

### Django

In your base template:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}{% endblock %}</title>
</head>
<body>
  {% block content %}{% endblock %}

  <footer>
    <script src="https://getsolokit.com/badge.js" defer></script>
    <div id="solokit-badge"></div>
  </footer>
</body>
</html>
```

### Astro

```astro
---
// SolokitBadge.astro
---
<div id="solokit-badge"></div>

<script>
  const script = document.createElement('script');
  script.src = 'https://getsolokit.com/badge.js';
  document.body.appendChild(script);
</script>
```

### Static HTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Project</title>
</head>
<body>
  <h1>My Project</h1>

  <footer>
    <script src="https://getsolokit.com/badge.js" defer></script>
    <div id="solokit-badge"></div>
  </footer>
</body>
</html>
```

## Styling

The badge inherits styles from its container. You can wrap it to control positioning:

```html
<div style="text-align: center; padding: 1rem;">
  <div id="solokit-badge"></div>
</div>
```

## How It Works

The badge script:

1. Loads asynchronously (doesn't block page rendering)
2. Detects system color scheme via `prefers-color-scheme`
3. Listens for theme changes and updates automatically
4. Injects a styled link pointing to getsolokit.com
