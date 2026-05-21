# V36800 Backend Test Checklist

1. Deploy backend only.
2. Do not deploy or modify frontend.
3. Confirm root endpoint returns `V36800-structured-execution-object-engine`.
4. Confirm `/health` returns status `ok`.
5. Confirm `/test-report` loads in browser.
6. Confirm `/test-report-json` returns `status: pass`.
7. Send POST `/run` with:
   ```json
   {
     "input": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
     "mode": "execution",
     "brain": "revenue",
     "output_type": "proposal",
     "depth": "standard"
   }
   ```
8. Confirm `/run` returns all required fields:
   - `executive_summary`
   - `next_move`
   - `decision`
   - `action_steps`
   - `ready_assets`
   - `risk`
   - `priority`
   - `recommended_command`
   - `execution_objects`
   - `primary_object`
   - `deployment_sequence`
   - `executive_scan`
9. Confirm `execution_objects` contains decision, action, asset, and risk objects.
10. Confirm frontend V37100 still points to the same backend URL.
