# Documentation Guide

This folder stores non-runtime project documentation.

## Structure

- `prompts/`: planning notes, requirements, environment setup, and architecture context.
- `PaperImages/`: thesis diagrams and exported images, including draw.io source files and PNG exports.
- `*.docx`: local thesis drafts and backups. These files are ignored by Git because Word drafts are large and change often.

## Thesis Notes

- Keep editable diagram sources (`.drawio`) together with their exported images (`.png`).
- Draw.io temporary backup files (`*.bkp`) and Word lock files (`~$*.docx`) should not be committed.
- During thesis formatting, temporary automation scripts can be placed under `tmp/`; this directory is ignored by Git.

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
