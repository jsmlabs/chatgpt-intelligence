---
title: Choosing the Right Response Format
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Choosing the Right Response Format

## In plain English
A good response is **easy to understand before it is visually impressive**. Choose text, tables, charts, diagrams, or interactions based on what the reader needs to accomplish.

## Product evidence
OpenAI documents GPT-6 Intelligent UI as combining text, visuals, and interactive elements in ChatGPT. Available experiences can differ by model, reasoning mode, plan, and client; GPT-6 Pro/Astra does not support Intelligent UI in the documented Chat experience. See [Intelligent UI in ChatGPT](https://help.openai.com/en/articles/20001598-intelligent-ui-in-chatgpt) and [GPT-6 models](https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt), reviewed 2026-11-06.

The following selection policy is **our proposed design guidance**, not a guaranteed internal component-selection algorithm.

## Design content first
1. Write the one-sentence answer or result.
2. Identify the essential evidence and constraints.
3. Group related points and determine the sequence.
4. Choose the simplest presentation that exposes the relationships.
5. Verify that users can still understand the answer without interacting with a visualization.

## Quick format guide
| Information need | Start with | Avoid |
| --- | --- | --- |
| Definition | One paragraph | Dashboard-like decoration |
| Exact comparison | Table with common criteria | Incomparable cards |
| Sequence | Numbered steps | Complex flowchart for two steps |
| Numerical change | Sourced chart with labels | Invented measurements |
| Spatial locations | Map when supported and relevant | Unnecessary map for abstract concepts |
| User-adjustable scenario | Real, supported controls | Buttons that do nothing |
| Drafting an email | Editable writing format when supported | A chart replacing the message |

## Example
**Question:** "What is context engineering?" Use a short explanation.

**Question:** "Compare context engineering, memory, and knowledge by purpose and lifetime." Use a three-row table because it exposes shared dimensions.

**Question:** "How would a quality score change if evidence were weighted more heavily?" A transparent interactive calculator may help, if the current environment actually supports one.

## Quality and accessibility
Keep meaningful text outside visuals, label units, avoid relying on color alone, and allow the explanation to stand on its own. Mobile users should not need to pan through a large collection of decorative cards.

## Failure cases
- UI is selected before the answer is understood.
- A chart includes fabricated values.
- An interactive surface suggests a real action but has no working callback.
- The design relies on features unavailable in the current client.
- A lengthy interface obscures qualifications and citations.

## Acceptance criteria
- The main answer is clear without decorative UI.
- Each component adds meaningful understanding or function.
- Data and limitations remain visible.
- Capability assumptions are verified for the applicable ChatGPT surface.

## Related reading
[Decision model](../architecture/intelligent-ui-decision-model.md) | [Response lifecycle](../architecture/response-lifecycle.md)
