# Contributing

We aim for explanations anyone can follow, without sacrificing technical accuracy.

## Before editing
1. Check whether the topic already has a canonical home.
2. Explain the subject plainly before introducing jargon.
3. Separate **officially documented behavior**, **observed behavior**, **inference**, and **proposal**.
4. Cite sources and verification dates for changeable product claims.
5. Use realistic but synthetic examples; do not publish private chat histories or personal memory data.

## Naming and structure
- Use English and descriptive `kebab-case.md` filenames.
- Use relative links between documents.
- Keep one primary owner per concept; link instead of copying material.
- Add directories only when they have useful content.
- Use the [document template](templates/document-template.md) when it helps. Do not add empty headings mechanically.

## Suggested status labels
`draft` (work in progress), `proposed` (ready for discussion), `accepted` (project design approved), `deprecated` (superseded). These labels do **not** prove that a ChatGPT capability exists.

## Review checklist
- Is the purpose clear in the opening paragraph?
- Would a first-time reader understand the terminology?
- Are factual claims appropriately sourced and dated?
- Are limitations and trade-offs explicit?
- Do examples and links work?
- Is this the simplest useful structure?


## G0 implementation guidance

- Python 3.11 standard library only for the G0 reference package.
- Keep validation, authorization, availability checks and execution distinct; do not derive permissions from models, source text or command flags.
- New generators register with `generators.foundation.Registry`; mark `AVAILABLE` only after implementing and verifying the host adapter.
- Use synthetic tests in `tests/test_generators.py`. A mock passing is not evidence that any external tool is operational.
- Do not introduce provider endpoints, publishing, API keys or generated artifacts during G0.
- [Runtime contract](architecture/generator-foundation.md) and [roadmap](GENERATOR-ROADMAP.md) are the sources of truth.
