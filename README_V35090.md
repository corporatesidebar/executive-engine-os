# Executive Engine OS — V35090 Stabilization Patch

## Baseline
Restored from V35080 package.

## Version
`35090-stabilization-patch`

## What changed
- Fixed `/run` quality patch request handling: `request` -> `req`.
- Fixed `/autonomous-package` quality patch request handling: `request` -> `req`.
- Added `sanitize_workspace()` compatibility shim so workspace cleanup routes no longer fail.
- Stabilized active context writes to use `ACTIVE_CONTEXT` consistently.
- Fixed local `now` timestamp shadowing in `/autonomous-package`.
- Preserved OpenAI-first routing and Claude fallback safety.
- Updated frontend version label to V35090 Stabilization.

## Verified locally
- Python compile: pass.
- `/health`: pass.
- `/debug`: pass.
- `/providers`: pass.
- `/test-report-json`: pass.
- `/quality-state`: pass.
- `/run`: pass with executive proposal input.
- `/autonomous-package`: pass with executive proposal input.

## Deployment
Upload this ZIP to GitHub/Render using the existing deployment structure.
Do not change Render service URLs.
