---
title: Intelligent UI Decision Model
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Intelligent UI Decision Model

## Overview
Choose the **best presentation for the information**, not the most visually complex one. First plan the content; then decide whether any UI component improves comprehension.

## Decision process
1. **Identify the task:** Explain, compare, navigate, analyze, decide, or interact.
2. **Design the information hierarchy:** Lead with the answer and group related facts.
3. **Assess content shape:** Short fact, exact comparison, numerical trend, multi-step process, spatial relationship, or interactive choice.
4. **Choose the minimum effective format:** Start with readable prose and introduce structured or visual components only for a demonstrated benefit.
5. **Check availability and accessibility:** Never assume a component exists in every model, plan, client, or message surface.
6. **Validate the result:** Ensure the reader can understand the answer without decorative UI and that visual elements do not obscure important caveats.

## Format guidance

| Information need | Preferred starting format | Caution |
| --- | --- | --- |
| Simple definition | Short paragraph | Avoid needless cards |
| Exact comparison | Table | Keep criteria consistent |
| Ordered workflow | Numbered steps or flow diagram | Avoid overspecification |
| Quantitative trend | Chart with labels and source | Never invent data |
| Multiple geographic stops | Map if supported and relevant | Do not invent routes or times |
| Choice requiring user interaction | Appropriate controls if supported | Controls must perform useful actions |

## Example
**Question:** What is context engineering? A short definition is sufficient.

**Question:** Compare context, knowledge, and memory. A three-row table can help distinguish their responsibilities.

## Failure modes
- Styling first, content second.
- Large image galleries for a text-only question.
- Interactive controls with no working behavior.
- Unsupported UI capability claims.
- Dense visual presentation that is hard to read on mobile.

## Acceptance criteria
- The central answer is present without relying exclusively on visualization.
- Each component adds information or useful interaction.
- Important source and uncertainty details remain visible.
- Unsupported components are not promised.

## Related
[Response lifecycle](response-lifecycle.md) | [Compatibility](chatgpt-compatibility.md) | [Intelligent UI](../intelligent-ui/README.md)
