---
title: Publication Safety Verification
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: verified-capability
---

# Scoped Public-Repository Safety Verification

## Objective
Provide a deterministic, bounded safety signal for accidental credential publication in tracked text files. This is an **internal automated scan**, not an independent privacy, legal, security, source-history or editorial audit.

## Implementation
- [Scanner](../scripts/check_publication_safety.py) enumerates committed files with `git ls-files`, only reads selected UTF-8 text formats, rejects oversized text files instead of silently skipping them, and reports signature categories without printing matching tokens.
- High-confidence signatures include private-key headers, classic and fine-grained GitHub tokens, OpenAI project API keys, AWS access key identifiers and Slack bot tokens.
- [Six regression tests](../tests/test_publication_safety.py) verify a clean sample, detected synthetic credentials, omitted secret values, skipped image extensions, and missing/oversized-file handling.
- Both the [development QA workflow](../.github/workflows/docs-quality.yml) and [strict release workflow](../.github/workflows/release-readiness.yml) invoke the scanner.

## Observed GitHub Actions evidence
[Run for commit `1d0d354`](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42210670991) completed successfully:
- **46 unit tests passed**.
- **111 tracked text files scanned; 0 signature findings**.
- **65 Markdown files; 410 relative links; 0 errors**.
- **56/56 original brand manifest entries verified**.
- Strict release readiness report: **4 unresolved conditions**.

## Limitations
- The scan does not inspect historical Git commits, untracked working files, binary-image contents, semantic PII, every secret format, text files over the configured safety limit, or external repositories.
- Zero findings is **not** proof that public content is private-data-free, compliant with trademark policy, independently edited, or secure.
- The release gate still requires a separate, independently evidenced editorial/privacy review.

[Quality standards](quality-standards.md) | [Phase 06 readiness](phase06-release-readiness.md) | [Roadmap](../ROADMAP.md)
