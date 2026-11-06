---
title: Local Verifier Execution
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# Local Verifier Execution - 2026-11-06

## Scope and provenance
Eight unit tests were executed in a local temporary environment using **manually reconstructed, functionally equivalent copies** of the currently published `scripts/check_docs.py`, `scripts/verify_branding_archive.py`, and `tests/test_quality_scripts.py`. The actual GitHub repository checkout was **not** available locally. This result must not be presented as a byte-identical checkout or GitHub Actions run.

## Observed results
| Check | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **passed - 8 tests, 0 failures, 0 errors** |
| Archive verification on supplied `chatgpt-intelligence-brand-v1.4-safe-import.zip` | **passed - 56 manifest files, 57 entries, SHA-256, size, CRC and paths** |
| Actual GitHub Actions job | **unverified** |
| Entire GitHub checkout documentation scan | **not-run** |
| Fresh-chat `/INTEL` E2E | **not-run** |
| Original binary asset publication | **blocked** |

## Important qualification
The eight tests exercise the expected behavior of the reconstructed local scripts. Their successful execution supports the test design but does **not** prove that the exact committed files or workflow pass in GitHub Actions. The ZIP verification used the actual supplied archive bytes, but the checker was reconstructed locally from the GitHub source.

The expected error messages printed by negative archive test cases are part of successful rejection tests; they are not unit-test failures.

## Next acceptance gate
Run the committed suite in an actual repository checkout or obtain a completed GitHub Actions run. Record the exact commit, workflow URL, job conclusion, and any failed assertions. Continue with [fresh-chat testing](intel-end-to-end-tests.md) and [binary asset installation](../guides/branding-integration.md).

[Roadmap](../ROADMAP.md) | [Evaluation guidelines](evaluation-guidelines.md)
