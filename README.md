# Executive Engine OS — V36510 Font Weight Fix

Frontend-only typography override.

## What this fixes

- Text looking too bold
- Response area feeling heavy
- Middle column being hard to read
- Generated content looking visually loud

## What this does NOT change

- Layout
- Navigation
- Sidebars
- Backend
- API URL
- Response contract

## Install

Put this file into:

```text
/frontend/font-weight-fix.css
```

Then load it after your existing CSS, or paste the contents at the very bottom of your existing CSS file.

Example:

```html
<link rel="stylesheet" href="./font-weight-fix.css">
```

Important: it must load AFTER the current/main CSS.
