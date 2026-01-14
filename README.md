# HappyApp

**Explainable mood inference from physiological data**

Now live at: https://swacziarg.github.io/HappyApp/#/login

HappyApp is a secure, multi-user web app that converts raw Garmin health data into personalized, explainable daily mood predictions.

---

## What it does

- Users upload Garmin exports (ZIP / JSON)
- Backend ingests and normalizes physiological data
- Personalized baselines are computed per user
- Daily features are inferred into a mood score (1–5)
- Users can add manual mood check-ins
- A React UI displays today’s mood and historical trends

---

## High-level flow

Garmin Export
→ Ingestion
→ Daily Features (personal baselines)
→ Mood Inference (rule-based)
→ Predictions API
→ React UI

---

## Tech stack

**Backend:** FastAPI, Supabase (Postgres + RLS)  
**Frontend:** React  
**Auth:** Supabase Auth (JWT)  
**Deployment:** Render + GitHub  
**Data:** Garmin exports (sleep, HRV, stress, activity, body battery)
