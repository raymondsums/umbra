"""The Umbra engine — generates the graph and finds gaps via the Claude API.

Each public function is an async generator yielding `(event, payload)` tuples,
which `main.py` turns into a Server-Sent Events stream so the graph builds
progressively on the frontend.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from models import DiscoveredTopic, ExpandResult, Gap, SeedResult, VerifyResult
from prompts import (
    ENGINE_SYSTEM,
    VERIFY_SYSTEM,
    expand_user_prompt,
    seed_user_prompt,
    verify_user_prompt,
)

MODEL = "claude-opus-4-7"

_client: AsyncAnthropic | None = None


def client() -> AsyncAnthropic:
    """Lazily construct the Anthropic client so the module imports without a key."""
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the environment
    return _client


def _system(text: str) -> list[dict]:
    """Wrap a system prompt with a cache breakpoint.

    `cache_control` caches this stable prefix across requests. Caching only
    activates once the prefix exceeds ~4K tokens (it silently no-ops below
    that) — as the engine prompt grows with rules and examples, caching
    starts paying off for free.
    """
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


async def seed(question: str) -> AsyncIterator[tuple[str, dict]]:
    """Generate the seed topic and its spokes for a question."""
    yield "status", {"message": "seeding the graph"}

    response = await client().messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_system(ENGINE_SYSTEM),
        messages=[{"role": "user", "content": seed_user_prompt(question)}],
        output_format=SeedResult,
    )
    result = response.parsed_output
    if result is None:
        yield "error", {"message": "the engine could not produce a seed topic"}
        return

    topic = result.topic
    yield "topic", topic.model_dump()
    for spoke in topic.spokes:
        yield "spoke", spoke.model_dump()
    yield "done", {}


async def expand(
    topic: str, discovered: list[DiscoveredTopic]
) -> AsyncIterator[tuple[str, dict]]:
    """Expand a topic into spokes, and precipitate any gaps against the graph."""
    yield "status", {"message": f"surveying {topic}"}

    response = await client().messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_system(ENGINE_SYSTEM),
        messages=[{"role": "user", "content": expand_user_prompt(topic, discovered)}],
        output_format=ExpandResult,
    )
    result = response.parsed_output
    if result is None:
        yield "error", {"message": f"the engine could not expand '{topic}'"}
        return

    yield "topic", result.topic.model_dump()
    for spoke in result.topic.spokes:
        yield "spoke", spoke.model_dump()
    for gap in result.gaps:
        yield "gap", gap.model_dump()
    yield "done", {}


async def verify(gap: Gap) -> AsyncIterator[tuple[str, dict]]:
    """Verify a gap by searching for work that would connect its two topics."""
    yield "status", {"message": "retrieving sources"}

    verdict_format = {"type": "json_schema", "schema": VerifyResult.model_json_schema()}

    async with client().messages.stream(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=_system(VERIFY_SYSTEM),
        messages=[{"role": "user", "content": verify_user_prompt(gap)}],
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        output_config={"format": verdict_format},
    ) as stream:
        async for event in stream:
            # Surface each web search to the frontend as progress.
            if event.type == "content_block_start":
                block = event.content_block
                if getattr(block, "type", None) == "server_tool_use":
                    yield "status", {"message": "searching the literature"}
        final = await stream.get_final_message()

    verdict = _parse_verdict(final)
    if verdict is None:
        # If web search hit its server-side loop limit, stop_reason is
        # "pause_turn" and there is no verdict yet — resume handling can be
        # added here later.
        yield "error", {"message": "verification did not return a verdict"}
        return

    yield "verdict", verdict.model_dump()
    yield "done", {}


def _parse_verdict(message) -> VerifyResult | None:
    """Pull the structured verdict out of the final message's text block."""
    for block in message.content:
        if getattr(block, "type", None) == "text":
            try:
                return VerifyResult.model_validate_json(block.text)
            except Exception:
                continue
    return None
