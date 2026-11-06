---
title: Research and Verification
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Research and Verification

## In plain English
Research turns an interesting question into an answer that others can **inspect, challenge, and update**. It should reveal limitations, not hide them.

## Practical research workflow
1. **Question:** State precisely what needs to be learned.
2. **Boundary:** Specify product, model, client, date, and population if relevant.
3. **Evidence:** Gather primary sources and direct observations where possible.
4. **Method:** Record how information was found or how tests would be run.
5. **Result:** Separate what was verified from what is merely plausible.
6. **Uncertainty:** Document known gaps and alternative explanations.
7. **Update trigger:** Decide what would require rechecking this finding.

## Example: Does Intelligent UI support every reasoning mode?
The question is answerable only when we distinguish the GPT-6 Chat experience from other products and modes.

As documented in [Intelligent UI in ChatGPT](https://help.openai.com/en/articles/20001598-intelligent-ui-in-chatgpt) (reviewed 2026-11-06), GPT-6 Chat supports Intelligent UI in specified modes, while the documented Pro/Astra reasoning option does not. This supports a **product documentation finding**, not a claim about an independently tested account or every future release.

## Reproducible evaluation plan
For a future test, hold the user task constant and record:
- ChatGPT product surface and client version
- Selected model and thinking level, when visible
- Account or workspace conditions relevant to availability
- Exact prompt, result description, and date
- Expected output and known confounders

Do not claim such a test was run unless its observed outcome is saved.

## Sample research record
```yaml
question: Does this ChatGPT surface support a specific UI format?
status: proposed
classification: experimental
tested_on: null
source_url: null
result: not-run
limitations:
  - Needs a controlled observation in a supported client.
```

## Common research errors
- Reporting a planned experiment as a result.
- Confusing rollout availability with universal access.
- Concluding causation from a single example.
- Omitting source publication dates and product boundaries.
- Treating one response's formatting as a deterministic rule.

## Acceptance criteria
- The question, evidence, method, result, and limitations are all visible.
- Existing sources can be followed without private credentials.
- Findings are appropriately scoped and dated.
- Unperformed experiments are labeled `not-run`.

## Related reading
[Evidence and Source Quality](../knowledge/evidence-and-source-quality.md) | [Compatibility](../architecture/chatgpt-compatibility.md)
