---
title: Release Gate Verification
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: verified-capability
---

# Release Gate Verification - 2026-11-06

## Implemented
- [`scripts/check_release.py`](../scripts/check_release.py): fail-closed structural readiness check (strict by default).
- [`quality/release-evidence.json`](release-evidence.json): machine-readable, intentionally `not-run` attestations until actual evidence exists.
- [`tests/test_release_gate.py`](../tests/test_release_gate.py): five negative tests for missing brand, missing client evidence, missing reference, missing domain, and invalid evidence JSON.
- [Documentation Quality workflow](../.github/workflows/docs-quality.yml): executes tests and logs readiness as `--report-only`, so incomplete release criteria do not stop development CI.

## Verified GitHub Actions result
[Workflow run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42206523537) for commit `0cad2744f84ddd7f693beaf36a3dd15b0083a77e` completed **success**. Its job log reports:
- **21 unit tests passed**.
- **59 Markdown files, 346 relative links, 0 errors**.
- **Release readiness: BLOCKED (5 unmet conditions)**.
- Remote branding manifest stage skipped because `branding/v1.4/MANIFEST.json` was absent.

The five reported release blockers were:
1. `branding/v1.4/MANIFEST.json` not published.
2. `fresh_chat_intel` not passed.
3. `intelligent_ui` not passed.
4. `brand_visual_review` not passed.
5. `independent_editorial_privacy_review` not passed.

## Interpretation and authority
- Strict `python scripts/check_release.py --root .` exits nonzero while structural conditions are unmet; `--report-only` prints the same failures but exits zero for routine CI.
- `status: passed` with a nonempty evidence reference is **a human attestation**, not cryptographic verification of a ChatGPT client or independent reviewer. Inspect the evidence manually before any release.
- Passing the structural gate is necessary but not sufficient for publishing a release. Release authorization and any branch/tag policy checks remain separate.
- A directory named `branding/v1.4/` was briefly created and deleted in other commits during this session; the verified Git tree afterwards had no published files under that path. This record does not attribute those actions or treat a directory-only commit as brand publication.

[Roadmap](../ROADMAP.md) | [Phase 06 review](phase06-release-readiness.md) | [Release evidence](release-evidence.json)
