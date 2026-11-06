---
title: Branding Accessibility Sampling
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# Branding v1.4 - Static Accessibility Sampling

## Scope
A **limited deterministic inspection**, not an independent WCAG conformance audit. Original brand files remain unchanged and manifest integrity is preserved. The evaluated background and foreground hex values come from [v1.4 design tokens](../branding/v1.4/design-system/tokens.json) and the [theme CSS](../branding/v1.4/design-system/theme-tokens.css). No live browser, keyboard navigation, assistive technology or target ChatGPT client was tested.

## Automated media checks
[GitHub Actions run for commit `9a9adc0`](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42223107435) passed the [brand media validator](../scripts/check_brand_media.py):
- **26 PNG files:** valid signature, PNG chunk CRCs, IHDR, IEND and absence of trailing data.
- **25 SVG files:** parseable XML with expected SVG root and numeric dimensions; embedded script and entity/DOCTYPE declarations rejected.
- **1 HTML preview:** static local `src` and `href` references exist.
- Paired PNG/SVG dimensions match; **0 detected media-format errors**.
- **61 regression tests passed** overall. Manifest byte hashes passed separately (56/56).

This does not test CSS layout, JavaScript toggle behavior, dynamic HTML assets, raster legibility, or rendered appearance in a browser.

## Computed contrast sampling
Calculated from the sRGB relative-luminance formula in [WCAG 2.2, SC 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum). The table rounds contrast ratios to two decimals.

| Foreground / background | Ratio | AA normal-text 4.5:1 |
| --- | ---: | --- |
| Light `text` / `bg` (`#171717` / `#FFFFFF`) | **17.93:1** | Pass |
| Light `muted` / `bg` (`#676767` / `#FFFFFF`) | **5.66:1** | Pass |
| Light `muted` / `surface` (`#676767` / `#F7F7F8`) | **5.28:1** | Pass |
| Dark `text` / `bg` (`#F9F9F9` / `#212121`) | **15.29:1** | Pass |
| Dark `muted` / `bg` (`#B4B4B4` / `#212121`) | **7.77:1** | Pass |
| Dark `muted` / `surface` (`#B4B4B4` / `#303030`) | **6.37:1** | Pass |
| Light `accent` / `bg` (`#0F8B72` / `#FFFFFF`) | **4.24:1** | **Below** threshold *if used for normal-sized text* |
| Dark `accent` / `bg` (`#2EAA91` / `#212121`) | **5.58:1** | Pass |

WCAG AA normal text generally requires 4.5:1; relevant non-text UI indicators generally require at least 3:1. The light accent is used for the preview's focus outline rather than evidenced as normal-sized text, so its **4.24:1 value is a conditional caution, not a demonstrated WCAG violation**. [W3C non-text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) applies when assessing the focus indicator against its actual adjacent background.

## Outstanding visual accessibility review
- Render both themes in the actual browser, including keyboard focus state and the light/dark switch.
- Check icon recognition at 16px/32px, actual font rendering, contrast in layered surfaces, zoom, narrow screens and assistive technology.
- Verify dark-mode README banner in actual GitHub client and ensure independent branding and naming review.
- Confirm that any future use of the light accent for body text meets the 4.5:1 criterion or adjust the specific usage (not the immutable source files without an approved package revision).

The `brand_visual_review` top-level release gate remains **not-run**. This is additional scoped evidence, not independent approval.

[Visual review](branding-visual-inspection.md) | [Publication evidence](branding-publication-verification.md) | [Phase 06 readiness](phase06-release-readiness.md)
