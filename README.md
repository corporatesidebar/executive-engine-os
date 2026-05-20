# Executive Engine OS — V36810 Structured Object Renderer Engine

Scope: FRONTEND ONLY.

Do not deploy this as a backend replacement. Backend, AI logic, /run, API URL, Supabase, and deployment structure are untouched.

## What changed
- Added frontend object detection layer.
- Added renderer router.
- Added execution package renderer.
- Added proposal renderer.
- Added CRM renderer.
- Added KPI renderer.
- Added outbound renderer.
- Added deployment / implementation / automation / delegation / workflow renderers.
- Preserved existing layout, sidebar, navigation, command box, colors, spacing, and typography.
- Legacy response fields still render, but are compressed behind expandable details.

## Deploy
Upload the contents of `/frontend` to the existing static frontend service.

## Backend response fields supported
- execution_objects
- execution_packages
- crm_system
- kpi_system
- outbound_systems
- deployment_sequence
- automation_stack
- implementation_plan
- proposal
- proposals
- pricing_structure
- delegation_map
- operational_workflows
- workflows
- sops
- onboarding_system
- hiring_system

## Rollback
Restore the previous frontend ZIP if the renderer does not match the backend payload.
