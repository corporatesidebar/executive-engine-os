# Executive Engine OS — V36600 Executive Cognition UI Engine

Frontend-only package.

## Purpose

Upgrade the response presentation layer from “AI card / project manager output” into an executive cognition briefing.

## What this does

- Adds a dominant insight visual hierarchy
- Reduces label dominance
- Makes response text less equalized
- Adds optional `renderExecutiveCognitionBrief(response)` helper
- Supports pressure / briefing / presence / reasoning engine response fields
- Preserves layout, sidebar, navigation, routes, API URL, and columns

## Install

Add this file after your existing CSS:

```html
<link rel="stylesheet" href="./executive-cognition-ui.css">
```

Optional renderer helper:

```html
<script src="./executive-cognition-ui.js"></script>
```

If you want to use the optional renderer, after `/run` returns JSON:

```js
responseContainer.innerHTML = window.renderExecutiveCognitionBrief(data);
```

## Important

This does NOT redesign the app shell.

Do NOT change:
- left nav
- right columns
- routing
- backend
- API URL
- deployment structure

This only improves the middle response cognition presentation.
