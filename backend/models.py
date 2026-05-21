"""Domain and API models for the Umbra engine.

Models tagged `extra="forbid"` double as structured-output schemas — that
config makes Pydantic emit `additionalProperties: false`, which the Claude
structured-outputs API requires.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GapType = Literal["ADJACENCY", "ASSUMPTION", "STALE", "RESOLUTION", "TRANSFER"]


# --- domain ---------------------------------------------------------------

class Spoke(BaseModel):
    """A candidate direction radiating from a topic."""
    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Short topic name, 1-3 words, lowercase")
    sub: str = Field(description="A brief qualifier shown under the label")
    note: str = Field(description="One sentence on why this direction is worth exploring")


class Topic(BaseModel):
    """A concept-level node in the knowledge graph."""
    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="Short topic name, 1-3 words")
    sub: str = Field(description="A brief qualifier shown under the label")
    summary: str = Field(description="Two sentences describing what this topic covers")
    spokes: list[Spoke] = Field(description="3-5 directions a curious explorer could take from here")


class Gap(BaseModel):
    """A knowledge gap between two topics."""
    model_config = ConfigDict(extra="forbid")

    gid: str = Field(description="Stable id, e.g. GAP-01")
    type: GapType
    bridge_a: str = Field(description="Label of the first topic the gap bridges")
    bridge_b: str = Field(description="Label of the second topic the gap bridges")
    statement: str = Field(description="What the gap is, in 1-2 sentences")
    confidence: int = Field(description="1-5: how sure the gap is real and genuinely unstudied")


# --- engine results (structured-output schemas) ---------------------------

class SeedResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: Topic


class ExpandResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: Topic
    gaps: list[Gap] = Field(
        description="Gaps that precipitate between this topic and the already-discovered topics"
    )


class VerifyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: Literal["verified", "flagged"]
    evidence: str = Field(description="Evidence of absence, or why the gap could not be confirmed")
    confidence: int = Field(description="1-5")


# --- API request bodies ---------------------------------------------------

class SeedRequest(BaseModel):
    question: str


class ExpandRequest(BaseModel):
    topic: str = Field(description="Label of the topic to expand")
    discovered: list[str] = Field(
        default_factory=list, description="Labels of topics already on the graph"
    )


class VerifyGapRequest(BaseModel):
    gap: Gap
