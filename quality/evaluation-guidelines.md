---
title: Evaluation Guidelines
status: proposed
version: 0.1.0
updated: 2026-11-06
---

# Evaluation Guidelines

## Manual evaluation
For each document or example, ask:
- Is the central question answered?
- Are relevant claims supported?
- Is uncertainty explicit?
- Can a beginner understand the opening?
- Is the structure easy to navigate?
- Does every visual element add information value?
- Are limitations and privacy boundaries included when needed?

## Example outcome record
```yaml
case: documentation-review-001
target: architecture/response-lifecycle.md
result: not-run
reviewed_on: null
notes: Manual review pending
```

## Future work
Develop repeatable scenarios for instruction conflicts, stale source material, memory limitations, and complex UI selection. A future benchmark should not imply automated execution until it is actually implemented.

## Conversational end-to-end checks
See the [INTEL End-to-End Test Plan](intel-end-to-end-tests.md). The listed scenarios are **not-run** until observed in the actual ChatGPT client. The repository documentation audit cannot substitute for those results.

## Scoring rubric
The [pattern evaluation rubric](pattern-evaluation.md) provides comparable scenarios, 0-2 criterion scores, critical failure gates, and a result record template. It is not an executed evaluation.

## Existing-chat source retrieval evidence
The [source smoke test](intel-source-smoke-test.md) records fetched GitHub paths and blob SHAs. It is narrower than a fresh-chat `/INTEL` end-to-end test and cannot be substituted for one.

## Automated documentation regression checks
The [local checker](../scripts/check_docs.py) validates Markdown file targets and supported frontmatter values. The [CI workflow](../.github/workflows/docs-quality.yml) runs it on main and pull requests and verifies the brand manifest only when the original package is present. A missing manifest is an explicit skip, not a successful branding publication. Review CI execution status separately.

## Verifier regression tests
[Regression tests](../tests/test_quality_scripts.py) cover valid and missing links, invalid frontmatter, fenced-code exclusions, valid branding archives, hash mismatches, extra files, and path traversal. The workflow invokes `python -m unittest discover -s tests -v`. Publishing these tests does not establish a passing CI result.
