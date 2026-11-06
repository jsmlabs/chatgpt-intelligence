---
title: Branding v1.4 Integration and Verification
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Branding v1.4 Integration

## Objective
Publish the complete original 56-file branded asset package and its manifest under `branding/v1.4/` without overwriting existing independent branding documentation. Maintain the distinction between independent branding and the native ChatGPT UI.

## Source
Uploaded archive `chatgpt-intelligence-brand-final-v1.4(1).zip`. The verified collision-safe import archive stores the original package under `branding/v1.4/`. Earlier draft archives used `branding/` directly; do not extract those over the current checkout. The original manifest covers 56 files plus `MANIFEST.json`.

## Controlled installation
1. Inspect current `main` and preserve unrelated changes.
2. Compare the existing `branding/README.md`, `BRAND-GUIDELINES.md`, and `design-system/` files with the original ZIP. Some were previously edited separately.
3. Check the ZIP first with `python scripts/verify_branding_archive.py chatgpt-intelligence-brand-v1.4-safe-import.zip`, then extract into a temporary directory. The 57 original files belong inside `branding/v1.4/`.
4. Validate all 56 manifest entries by byte length and SHA-256. Reject unsafe paths and unexplained extra or missing files.
5. Keep the original 57 files intact in `branding/v1.4/`; this avoids collisions with the existing brand overview, guidelines, and tokens.
6. Copy the complete approved package into `branding/v1.4/`; run `python scripts/verify_branding.py branding/v1.4` against the actual checkout, and check the staged diff for unintended changes.
7. Commit and push only authorized files to `main`, respecting repository protection.
8. Read back binary and text files from the exact pushed revision and inspect visual appearance.

## Suggested local checks
```bash
python scripts/verify_branding.py branding/v1.4
git status --short
git diff --check
git diff --cached --stat
```

**Important:** `git diff` alone does not verify local ZIP installation. Check actual file paths and hashes first. Previously passed checks should not be rerun without cause.

## Status
Original archive and collision-safe import verification: **passed locally, 56/56 checks and 57 original files**. Remote binary upload: **not completed**. Current GitHub text writes cannot substitute for binary publication. The branded HTML preview is a static demonstration, not a native ChatGPT theme.

## Acceptance
The final GitHub revision contains the original 57 files under `branding/v1.4/` with validated bytes, no unintended overwrites, documented attribution, and successful image/preview inspection.

[Branding status](../branding/README.md) | [Roadmap](../ROADMAP.md) | [INTEL activation](chatgpt-activation.md)
