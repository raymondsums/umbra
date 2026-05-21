"""Umbra engine — FastAPI app.

Run:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from dotenv import load_dotenv

load_dotenv()  # load ANTHROPIC_API_KEY from .env before the engine imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import engine
from models import ExpandRequest, SeedRequest, VerifyGapRequest

app = FastAPI(title="Umbra Engine", version="0.1.0")

# The frontend (the prototype HTML) runs from a file:// URL or a dev server.
# Allow everything in development; tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(source: AsyncIterator[tuple[str, dict]]) -> StreamingResponse:
    """Wrap an (event, payload) async iterator as a Server-Sent Events stream."""

    async def gen() -> AsyncIterator[str]:
        try:
            async for event, payload in source:
                yield f"event: {event}\ndata: {json.dumps(payload)}\n\n"
        except Exception as exc:  # surface engine/API failures to the client
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/seed")
async def seed(req: SeedRequest) -> StreamingResponse:
    """Seed a graph from a question. Streams the seed topic and its spokes."""
    return _sse(engine.seed(req.question))


@app.post("/expand")
async def expand(req: ExpandRequest) -> StreamingResponse:
    """Expand a topic. Streams the topic, its spokes, and any gaps that precipitate."""
    return _sse(engine.expand(req.topic, req.discovered))


@app.post("/verify-gap")
async def verify_gap(req: VerifyGapRequest) -> StreamingResponse:
    """Verify a gap with literature retrieval. Streams search progress and a verdict."""
    return _sse(engine.verify(req.gap))
