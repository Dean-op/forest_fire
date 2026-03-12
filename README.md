# Forest Fire Early Warning System

This repository contains a frontend + backend demo system for forest fire monitoring, alerting, and operator workflow handling.

## Project Layout

- `forest_fire_backend/`: FastAPI backend, AI inference, alerts, database access.
- `forest_fire_backend/media/`: local demo videos and alarm audio assets.
- `forest_fire_frontend/`: Vue 3 frontend dashboard and management UI.
- `docs/`: non-runtime documentation.

## Quick Start

### Backend

```powershell
cd D:\AllProjectFile\forest_fire\forest_fire_backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### Frontend

```powershell
cd D:\AllProjectFile\forest_fire\forest_fire_frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Documentation

- Main docs index: `docs/README.md`
- Planning and requirement notes: `docs/prompts/`

## Notes

- Keep runtime assets (models, database files) in their current locations unless path dependencies are updated together.
- Put local videos/audio under `forest_fire_backend/media/`.
- Temporary automation artifacts are excluded (for example, `.playwright-cli/`).
