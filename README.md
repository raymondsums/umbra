# Umbra

A visual knowledge gap explorer.

Umbra maps a field of knowledge as a graph and surfaces its *gaps* — the
questions nobody has connected yet. You start from a question, follow spokes
into related topics, and watch gaps precipitate on their own in the unlit
space between the ideas you have uncovered.

## Concept

- **Question-seeded** — exploration starts from a single question.
- **Spokes** — each topic radiates labelled spokes; tap one to travel into it
  and fan the graph outward.
- **Emergent gaps** — when two topics on your map are related but unconnected,
  a gap (`?`) precipitates between them. Gaps are never pre-placed.
- **Verify → hone → fill** — inspect a gap, verify the absence is real
  (retrieval finds zero connecting sources), and hone it into a direction.

The name: an *umbra* is the dark core of a shadow. Umbra is a map of what is
*not* known — you explore by illuminating the dark.

## Run it

Open `index.html` in any modern browser. No build step, no dependencies.

## Status

Early prototype. A single self-contained HTML file. It ships with one
hand-authored knowledge map ("trust in AI agents") to demonstrate the
interaction model. The real Umbra would generate the graph live from any
question via an LLM engine — that engine is not yet built.
