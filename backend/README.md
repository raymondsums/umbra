# Umbra Engine

The backend "engine" for Umbra — a FastAPI service that generates the knowledge
graph and finds gaps via the Claude API.

## Endpoints

All three POST endpoints stream Server-Sent Events, so the graph builds
progressively on the frontend.

- `POST /seed` — seed a graph from a question → `topic`, `spoke` events
- `POST /expand` — expand a topic into spokes; precipitate gaps → `topic`, `spoke`, `gap` events
- `POST /verify-gap` — verify a gap with literature retrieval → `status`, `verdict` events
- `GET /health`

## Run

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # then add your ANTHROPIC_API_KEY
    uvicorn main:app --reload --port 8000

## Try it

    curl -N -X POST localhost:8000/seed \
      -H 'content-type: application/json' \
      -d '{"question": "how do AI agents earn user trust?"}'

## Layout

    main.py        FastAPI app + SSE endpoints
    engine.py      the engine — Claude API calls (Opus 4.7, adaptive thinking)
    prompts.py     system prompts — the engine's "grammar" (cached prefix)
    models.py      Pydantic domain + request models / structured-output schemas

## Status

Scaffold. The endpoints work and call Claude, but the prompts in `prompts.py`
are a first draft — the quality of the gaps depends almost entirely on them,
and tuning them is the real work. The cache breakpoint on the system prompt
only activates once that prompt grows past ~4K tokens.
