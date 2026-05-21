# V37200 Test Checklist

## Backend
[ ] Deploy backend only
[ ] GET /health returns V37200
[ ] POST /run works
[ ] POST /run returns execution_objects
[ ] GET /workspace shows saved threads
[ ] GET /workspace/ready shows ready assets

## Frontend compatibility
[ ] Frontend still posts to /run
[ ] Required V36800 fields still exist
[ ] execution_objects render in frontend
[ ] No layout changes

## Persistence
[ ] Object appears after /run
[ ] Object status can be updated
[ ] Object can be archived
