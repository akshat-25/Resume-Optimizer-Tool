# Resume Tailor

Local-first resume analysis and tailoring app.

## Stack

- Frontend: Angular
- Backend: Python + FastAPI
- Local LLM: Ollama, recommended `qwen3:8b`
- Parsing/scoring: regex, YAKE, RapidFuzz, optional sentence-transformers embeddings

## Recommended Local Models

```bash
ollama pull qwen3:8b
ollama pull gemma3:4b
```

Use `qwen3:8b` as the default model on a MacBook Air M4 with 16 GB RAM. Use `gemma3:4b` as a faster fallback.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend still works without Ollama. It will return deterministic parsing, ATS checks, scores, keyword gaps, and rule-based suggestions. When Ollama is running, it also generates local LLM before/after rewrites.

## Frontend

```bash
cd frontend
npm install
npm start
```

Open `http://localhost:4200`.

## API

- `GET /api/health`
- `GET /api/models/local`
- `POST /api/resume/extract-text`
- `POST /api/analyze`

