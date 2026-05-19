# Executive Engine OS — V36100 Test Checklist

## Backend

### 1. Health
Open:
```text
GET /health
```

Expected:
```json
{
  "status": "ok",
  "version": "v36100-executive-workflow-intelligence"
}
```

### 2. Root
Open:
```text
GET /
```

Expected:
- product name
- version
- protected routes

### 3. Run Command
POST:
```json
{
  "input": "Build a proposal for an Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
  "mode": "proposal",
  "depth": "standard"
}
```

Expected response includes:
- next_move
- decision
- action_steps
- ready_assets
- risk
- priority
- recommended_command
- pressure
- mode
- operating_state
- follow_up_questions

## Frontend

### 1. Page loads
Expected:
- calm executive UI
- command input visible
- mode buttons visible
- output panel visible

### 2. Command submit
Expected:
- command sends to backend
- output sections populate
- recent decisions update
- active risks update
- ready assets update

### 3. Mode switching
Expected:
- Meeting / Proposal / Execution / Strategy / Decision buttons change mode
- command output reflects selected mode

### 4. No dashboard bloat
Expected:
- no fake charts
- no meaningless widgets
- no SaaS clutter

## Product Fit Test

Ask:
```text
I have a client meeting tomorrow with a dealership owner. I need to win a marketing retainer and show them why they are losing leads.
```

Expected:
- meeting intelligence
- proposal framing
- risks
- next move
- ready assets
- recommended follow-up command
