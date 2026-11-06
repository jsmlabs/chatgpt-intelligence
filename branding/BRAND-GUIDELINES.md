# ChatGPT Intelligence - Brand Guidelines v1.4.0

**Status:** Original independent branding design, integrated as project documentation
**Design direction:** ChatGPT Native / neutral and restrained
**Affiliation:** Independent; not officially affiliated with OpenAI

## Identity
- Name: **ChatGPT Intelligence**, the existing project name.
- Descriptor: **Independent research & design**.
- Positioning: Independent research and documentation for understanding, structuring, and designing better ChatGPT experiences.
- One-line statement: *Clarity, structure and design for better ChatGPT experiences.*
- Voice: clear, precise, calm, evidence-led, accessible.

## Original mark
The original supplied identity is formed by two stacked rounded rectangles and three dots, representing conversation, structured context, and continuing inquiry. It is **not** an OpenAI icon.

The supplied v1.4.0 package provides light, dark, and monochrome versions:
- `logos/`: symbols, lockups, and wordmarks in SVG and PNG.
- `icons/`: dark/light app icons in seven dimensions from 16px to 1024px.
- `banners/`: README hero images in light and dark.
- `social/`: GitHub social cards.
- `preview/`: static HTML mockup with theme toggle.

Keep 1/4 of the icon width as clear space. Preserve original vector proportions, colors, and legibility. Do not distort, add gradients, or recolor only part of the mark.

## Theme and layout
The colors are **project-defined approximations**, not extracted or official OpenAI design tokens. See [tokens.json](design-system/tokens.json) and [theme-tokens.css](design-system/theme-tokens.css).

| Role | Light | Dark |
| --- | --- | --- |
| Background | `#FFFFFF` | `#212121` |
| Sidebar | `#F9F9F9` | `#171717` |
| Surface | `#F7F7F8` | `#303030` |
| Primary text | `#171717` | `#F9F9F9` |
| Secondary text | `#676767` | `#B4B4B4` |
| Border | `#E5E5E5` | `#424242` |
| Optional interactive accent | `#0F8B72` | `#2EAA91` |

Use 4/8/12/16/24/32px spacing, 8/12/18px radii, system fonts, restrained typography, visible keyboard focus, subtle borders, and quiet backgrounds. Avoid glow, gradients, decorative network motifs, and needless UI cards.

## Source package and binary publication
The attached `chatgpt-intelligence-brand-final-v1.4` archive contains 56 manifest-listed files and the manifest. The asset package was independently checked for size and SHA-256 consistency. **Some binary assets cannot be published through the current text-file GitHub workflow and may still be absent from `main`**. Do not link to files as published without verifying their presence. Preserve the package's exact binary bytes and paths when uploading.

## ChatGPT integration boundary
Branding assets only illustrate this independent project. They cannot change the native ChatGPT UI. The proposed `/INTEL` activation convention uses the repository as a reference library and adapts ChatGPT output format using available UI primitives; see [Command Reference](../COMMANDS.md).

## Trademark and accuracy
The project contains the ChatGPT trademark in its repository name, but is not endorsed, sponsored, or operated by OpenAI. Independently verify legal suitability for public product use using [OpenAI brand guidelines](https://openai.com/brand/). Do not claim a pixel-perfect clone or official styling.

## Validation
The original package had complete raster and vector exports, theme tokens, preview, and a manifest. Exact binary asset publication and final client-side visual review remain separate checks.


## Canonical archive placement
The original ZIP package is retained without altered bytes under the planned `branding/v1.4/` directory. The files in this guideline and the root of `branding/` are project integration documentation and should not be confused with manifest-verified originals. The full archive is not yet published remotely.
