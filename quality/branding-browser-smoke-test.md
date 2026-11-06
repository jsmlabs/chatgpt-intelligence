---
title: Branding Browser Smoke Test
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# Branding v1.4 - Scoped Chromium Browser Smoke Test

## Method
On 2026-11-06, the actual supplied brand v1.4 ZIP was extracted to an isolated temporary directory and the original `preview/brand-showcase.html` source was inspected. Chromium was used through Playwright. The tool environment blocked direct navigation to both `file://` and an isolated `http://127.0.0.1` development server with `ERR_BLOCKED_BY_ADMINISTRATOR`.

To proceed without changing the published assets, the HTML content was loaded using Playwright `page.set_content` with the original, exact `design-system/theme-tokens.css` text inlined at its former stylesheet link. **The inline JavaScript was not modified.** This is a limited DOM/CSS/JS behavioral test, not a test of network, filesystem asset loading or fully equivalent browser navigation.

## Observed Chromium results
| Check | Desktop 1440×900 | Mobile 390×844 |
| --- | --- | --- |
| Initial `data-theme` | `light` | `light` |
| Initial button label | `Dark mode` | `Dark mode` |
| Sidebar visible | Yes | No (responsive CSS) |
| Horizontal document overflow | No | No |
| Click theme toggle | `data-theme=dark` | `data-theme=dark` |
| Dark-mode button label | `Light mode` | `Light mode` |
| Dark icon source assigned | `../icons/app-dark-64.png` | Same |
| Click toggle again | Returned to light | Returned to light |
| JavaScript page errors | 0 | 0 |

The relative icon paths and other static assets exist according to the independent [brand media format check](branding-accessibility-sampling.md). **No claim is made that the browser actually loaded those files in this test**, because the navigation/scheme restrictions prevented an end-to-end resource-loading check.

## Limitations and follow-up
- This test did not use the complete original page through ordinary browser navigation: CSS was inlined, and relative image loading was not verified.
- No screenshot-based visual diff, full 200% zoom/keyboard audit, screen reader inspection, focus-outline appearance capture or actual GitHub dark-mode banner render was performed.
- The browser environment restrictions are a **test-environment limitation**, not proof of a product defect.
- A complete visual accessibility and trademark review still requires independent human judgment and real target-client/browser evidence.
- Consequently `brand_visual_review` remains `not-run` in the release evidence ledger, although the limited component interaction cases above passed.

[Phase 06 review](phase06-release-readiness.md) | [Branding visual review](branding-visual-inspection.md) | [Roadmap](../ROADMAP.md)
