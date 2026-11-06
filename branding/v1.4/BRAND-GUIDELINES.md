# ChatGPT Intelligence - Brand Guidelines v1.4.0

**Status:** Completed design deliverable / independent project identity  
**Design direction:** ChatGPT Native / neutral and restrained  
**Repository:** Not modified

## 1. Identity

- Name: **ChatGPT Intelligence** (existing repository name, retained as instructed).
- Descriptor: **Independent research & design**.
- Extended positioning: *An independent documentation and research project for understanding, structuring and designing better ChatGPT experiences.*
- One-line statement: *Clarity, structure and design for better ChatGPT experiences.*
- Brand voice: clear, precise, calm, evidence-led, accessible.
- Independence: never imply affiliation, sponsorship, endorsement or official OpenAI status.

## 2. Logo and icon

The custom mark consists of **two stacked rounded rectangles**, with the front panel containing **three dots**. It represents conversation, structured context, and continuous inquiry.

Variants:
- `logos/wordmark-light.*` and `logos/wordmark-dark.*`: full wordmark with descriptor.
- `logos/lockup-light.*` and `logos/lockup-dark.*`: compact horizontal lockup.
- `logos/symbol-light.*`, `logos/symbol-dark.*`, and `logos/symbol-monochrome.*`: standalone symbol.
- `icons/app-{light|dark}-{16|32|64|128|256|512|1024}.*`: square icons.

Use the SVG master for scaling. Use pre-rendered PNGs for platforms that do not accept SVG. Never recolor only part of the symbol, distort it, or apply gradient/glow. Keep **at least 1/4 of icon width** as clear space around the standalone icon. Use full wordmark only when the rendered name remains legible.

**Important:** These identity assets are original *project designs*, not OpenAI marks, official ChatGPT assets, or a pixel-for-pixel reproduction of the live product.

## 3. Themes and colors

The system is a **project-defined approximation** of a ChatGPT-like neutral aesthetic, not a captured set of official OpenAI tokens.

| Token | Light | Dark |
| --- | --- | --- |
| Background | `#FFFFFF` | `#212121` |
| Sidebar | `#F9F9F9` | `#171717` |
| Surface | `#F7F7F8` | `#303030` |
| Primary text | `#171717` | `#F9F9F9` |
| Secondary text | `#676767` | `#B4B4B4` |
| Border | `#E5E5E5` | `#424242` |
| Optional interactive accent | `#0F8B72` | `#2EAA91` |

Use a system font stack; prefer inherited host fonts inside native integrations. Avoid bright accent-colored backgrounds, glows, gradients, 3D embellishments and decorative networking motifs. Theme variables live in `design-system/theme-tokens.css`.

## 4. Layout

- Spacing: 4 / 8 / 12 / 16 / 24 / 32 px.
- Corner radius: 8 / 12 / 18 px; pill only for controls intended to be pills.
- Typographic hierarchy: strong page heading, restrained subheading, readable body text, muted metadata.
- Sidebar: quiet background, subtle selected state, concise navigation.
- Main content: comfortable measure, generous vertical breathing room, no decorative cards around every section.
- Icons: monochrome outlines with consistent weight.
- Interactions: contrast visible in both themes, keyboard focus indicators, explicit labels.

## 5. Asset use

| Use | File |
| --- | --- |
| Repository social image | `social/github-social-dark.png` (1280×640), or Light |
| README cover | `banners/readme-hero-light.png` (1600×520), or Dark |
| Profile/app icon | `icons/app-dark-512.png` (512×512), or Light |
| Brand lockup | `logos/lockup-light.svg`, or Dark |
| Responsive visual sample | `preview/brand-showcase.html` |
| CSS variables | `design-system/theme-tokens.css` |
| JSON tokens | `design-system/tokens.json` |

## 6. Compatibility and legal notes

The visual direction is inspired by ChatGPT's minimal interface principles, but layout/color dimensions **have not been pixel-matched** against an authenticated, dated capture of its current UI. Only a neutral likeness is intended.

OpenAI's published brand guidelines claim ownership of the **ChatGPT** name and discourage using OpenAI marks to create confusing brands or implying endorsement. Because this project's existing name includes ChatGPT, **trademark clearance is outstanding for public brand/product usage**. This is a material publication consideration; the delivered assets are not a legal clearance or endorsement.

Official sources, reviewed 2026-11-06:
- https://openai.com/brand/
- https://developers.openai.com/plugins/concepts/ui-guidelines

## 7. Acceptance and verification

- All SVG and PNG variants exported.
- All SVG files validated by parsing and re-rendering.
- All PNG dimensions and opening checked.
- Light/dark and manifest completeness checked.
- Repository unchanged.
- Brand appearance is a design deliverable, not user-approved final taste or a verified 1:1 clone.
