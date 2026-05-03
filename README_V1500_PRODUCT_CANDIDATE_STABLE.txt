EXECUTIVE ENGINE OS — V1500 PRODUCT CANDIDATE STABLE

Built from V1450. Includes V1350, V1400, V1450, and V1500 work.

Adds:
- GET /product-candidate-status
- GET /product-candidate/checklist
- GET /v1500-milestone
- Frontend Candidate Status page

Preserved:
- /test-report
- /test-report-json
- /stable-version
- /product-dashboard
- /workflow-dashboard
- /intelligence-board
- /operator-console
- /health
- /diagnostic
- /system-test
- /run

No Supabase schema change. No OAuth activation. No external writes.

Test:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/product-candidate-status
https://executive-engine-os.onrender.com/product-candidate/checklist
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/v1500-milestone

Expected frontend badge:
V1500 Product Candidate Stable · V1500 Backend

Backend compile check:
PASS
