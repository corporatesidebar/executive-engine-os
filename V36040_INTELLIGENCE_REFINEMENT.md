# V36030 File Structure

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

## Rules

- Keep root clean.
- Do not store old ZIP files in repo.
- Do not store screenshots in repo unless needed.
- Do not create multiple duplicate recovery docs.
- Keep version notes inside `/docs`.
- Keep active app files in `/backend` and `/frontend`.
- Keep database files in `/database`.
