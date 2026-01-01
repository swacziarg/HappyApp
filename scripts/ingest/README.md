## Ingestion Philosophy

- Raw Garmin exports are never edited manually
- All normalization happens in code
- All imports are idempotent
- One row per user per day per table

## Supported Inputs

- Garmin sleep CSV
- Garmin daily physiology JSON

## Non-goals

- No API calls
- No ML logic
- No FastAPI dependencies
