# Finance Agent Task Runner

## Project Overview

Finance Agent Task Runner is a small full-stack prototype for a finance workflow agent. It accepts a natural-language request, extracts an invoice ID, looks up invoice, purchase order, and policy data, and returns a final answer plus an execution trace.

The backend exposes a FastAPI API. The frontend is a React application built with Vite for submitting requests and inspecting traces.

## Tech Stack

- Backend: Python 3.13, FastAPI, Uvicorn
- Backend testing: Pytest
- Frontend: React 18, React DOM, Vite
- Styling: CSS
- Data source: Local JSON files

## Prerequisites

- Python 3.13+
- Node.js 18+
- npm

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm install
```

## How To Run

Start the backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --app-dir src
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm run dev
```

The frontend runs on `http://localhost:5173`.
The backend runs on `http://localhost:8000`.

## How To Run Tests

Backend tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

## API Endpoints

### `GET /health`

Health check endpoint.

### `POST /agent/run`

Runs the finance agent workflow for a user request.

### `GET /agent/traces/{trace_id}`

Returns the execution trace for a previous run.

## Example Request

### `POST /agent/run`

```json
{
  "userRequest": "Please check invoice INV-1001. Why is it not paid yet?"
}
```

Example `curl`:

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "userRequest": "Please check invoice INV-1001. Why is it not paid yet?"
  }'
```

## Project Structure

```text
.
├── ARCHITECTURE.md
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── src/app/
│   │   ├── agent/
│   │   ├── api/
│   │   ├── data/
│   │   ├── domain/
│   │   ├── repositories/
│   │   ├── tools/
│   │   ├── factory.py
│   │   └── main.py
│   └── tests/
├── doc/
│   └── finance_agent_core_objects_architecture.pdf
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx
        ├── main.jsx
        └── styles.css
```
