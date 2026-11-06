---
title: G2.3 THEME deterministic generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G2.3 - THEME Generator

The local THEME runtime generates **JSON design tokens** or **CSS custom
properties** for a pair of light/dark color systems. It uses Python 3.11
standard library only and requires the trusted CREATE permission.

## Implemented contract

- Input: bounded `objective`, `preset` (`graphite`, `ocean`, `plum`,
  `forest`), optional exact opaque six-digit hex `accent`, and `format`
  (`json` or `css`). Extra fields fail closed.
- Output: deterministic role-based color tokens for light/dark, a spacing
  scale, system font family and radius token. JSON follows a **DTCG-style**
  `$type` / `$value` structure; it is not claimed to implement the full
  DTCG standard.
- CSS: token variables under `:root` and `[data-theme="light"]`; automatic
  dark mode via `prefers-color-scheme`, and explicit
  `[data-theme="dark"]` override. No remote fonts or assets.
- Algorithm: W3C sRGB relative luminance with the **0.04045** breakpoint
  and contrast ratio `(Llighter + 0.05)/(Ldarker + 0.05)`. Contrast
  conditions apply to each listed pair **before rounding**.
- Audit: normal text AA 4.5:1, non-text AA 3:1, and separate normal text
  AAA 7:1 check for the main text/background pair. Large text AA 3:1
  and AAA 4.5:1 thresholds follow the standard but are not substituted
  for the stronger normal-text rules used by the generator.
- Safety: token inputs cannot create CSS declarations, URLs or file paths;
  only vetted semantic roles and hex colors reach CSS. Exports require a
  trusted existing directory and an exclusive new `.json` or `.css`
  filename, with readback SHA-256 verification.

The authoritative specification is
[WCAG 2.2](https://www.w3.org/TR/WCAG22/#contrast-minimum),
[non-text contrast 1.4.11](https://www.w3.org/TR/WCAG22/#non-text-contrast)
and [the W3C relative-luminance formula](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum).
Consulted on 2026-11-06.

## Local CLI

Generate tokens, with the report printed to stderr and the artifact to
stdout:

```powershell
python -m generators theme --objective "Signal research dark/light UI" --preset graphite --format json --authorize-create
```

For a CSS file, create an export directory outside the repository, then:

```powershell
python -m generators theme --objective "Signal research UI" --preset plum --accent "#8159D5" --format css --authorize-create --export-root "$env:USERPROFILE\Desktop\Projects\INTEL-Outputs" --filename research-theme.css
```

A prior file is **never overwritten**. Using `--format json` requires
a `.json` filename; `--format css` requires `.css`.

## ChatGPT MCP

The additive `generate_theme` tool accepts the same four request
fields and returns JSON or CSS source text plus manifest and exact
contrast-pair audit evidence. It requires the host process to have
`--allow-create` and does **not** export a file via MCP. Default discovery
contains 11 tools, or 12 with explicitly enabled ComfyUI inference.
The `generate_design` tool remains independent.

## Acceptance limits

Each pair in `contrast_audit.pair_results` includes both role names,
mode, raw-based measured contrast (rounded only for reporting),
threshold, type and Boolean pass. The generator validates only
**enumerated opaque color pairs**. The following are **not** verified:

- Translucency, gradients, images behind text, actual font size/weight,
  or every foreground/background combination across a real UI.
- Keyboard navigation, focus visibility geometry, usability, reduced
  motion implementation or any other WCAG success criteria.
- A browser screenshot, human design approval or WCAG conformance.

An AA pass on these color pairs does not certify a design or website.
Future THEME integration may apply tokens to the DESIGN HTML prototype
after a separate acceptance check, but G2.3 does not change G2.2 rendering.

[DESIGN generator](design-generator.md) |
[Generator roadmap](../GENERATOR-ROADMAP.md) |
[Foundation contracts](generator-foundation.md)
