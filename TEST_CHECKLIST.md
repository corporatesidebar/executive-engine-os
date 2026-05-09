# Executive Engine OS — V36030 Cleanup + Architecture Stabilization

This package is a cleanup/stabilization build.

It is intentionally **not** a feature expansion.

## Purpose

Keep the project from becoming messy while preserving the current working system.

## Clean structure

```text
/backend
  main.py
  requirements.txt

/frontend
  index.html

/database
  supabase_schema.sql

/docs
  README.md
  CHANGELOG.md
  TEST_CHECKLIST.md
  ROLLBACK.md
  PRODUCT_VISION.md
  FILE_STRUCTURE.md

render.yaml
```

## Preserved

The build preserves the active backend, active frontend, Render config, and database folder.

Protected backend routes remain:

```text
/run
/health
/debug
/providers
/test-report-json
/db-status
/demo-state
/memory
/operating-layer
/daily-use
/how-to-use
```

## Removed from package

This cleanup package excludes old duplicate recovery docs, extra generated notes, temporary files, and old build clutter.

## Upload rule

Upload this ZIP as the clean repo structure only after backing up the current GitHub repo.
