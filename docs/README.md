# Documentation Guide

This folder stores non-runtime project documentation.

## Structure

- `prompts/`: planning notes, requirements, environment setup, and architecture context.

## Runtime Entry (for demo/defense)

- Backend: `forest_fire_backend/`
- Backend media assets: `forest_fire_backend/media/`
- Frontend: `forest_fire_frontend/`

Quick start:

```powershell
# backend
cd D:\AllProjectFile\forest_fire\forest_fire_backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8010
```

```powershell
# frontend
cd D:\AllProjectFile\forest_fire\forest_fire_frontend
npm run dev
```

Open: `http://127.0.0.1:5173`
