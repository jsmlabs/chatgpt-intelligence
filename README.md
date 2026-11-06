<picture>
  <source media="(prefers-color-scheme: dark)" srcset="branding/v1.4/banners/readme-hero-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="branding/v1.4/banners/readme-hero-light.png">
  <img src="branding/v1.4/banners/readme-hero-light.png" alt="ChatGPT Intelligence - Independent research and design" width="1600">
</picture>

# ChatGPT Intelligence

> Research, concepts, prompts, knowledge, memory, context engineering, and intelligent UI principles for high-quality, personalized ChatGPT experiences.

**Research with evidence. Design with intention. Build better ChatGPT interactions.**

An independent, open knowledge base for **understanding ChatGPT and designing clearer, more reliable, context-aware experiences**. Explore seven connected domains through practical guides, reusable prompts, documented design patterns and explicit capability boundaries.

**7 knowledge domains** · **6/6 documentation phases complete** · **Maintenance mode**

[**Get started**](GETTING_STARTED.md) · [**Explore the knowledge base**](#seven-knowledge-domains) · [**Use /INTEL**](#use-intel) · [**Architecture**](architecture/overview.md) · [**Project status**](#project-status)

---

## Choose your starting point

| Your goal | Recommended path |
| --- | --- |
| Get oriented in five minutes | [Getting Started](GETTING_STARTED.md) |
| Ask source-grounded questions using the documented command convention | [Use `/INTEL`](#use-intel) |
| Write clearer, more reusable instructions | [Prompt Patterns](prompts/prompt-patterns.md) |
| Decide what information and context actually matter | [Context Selection](context-engineering/context-selection.md) |
| Present answers with useful structure and UI | [Intelligent UI Patterns](intelligent-ui/response-patterns.md) |
| Assess evidence, accuracy and limitations | [Quality Standards](quality/quality-standards.md) |

## Seven knowledge domains

The domains are connected, but each can be explored independently.

| Domain | What it helps you do | Explore |
| --- | --- | --- |
| **[Research](research/README.md)** | Investigate questions, verify sources and represent uncertainty | [Research method](research/research-method.md) |
| **[Concepts](concepts/README.md)** | Develop ideas and evaluate alternatives and trade-offs | [Concept development](concepts/concept-development.md) |
| **[Prompts](prompts/README.md)** | Create clear instructions, reusable workflows and output contracts | [Prompt design](prompts/prompt-design.md) |
| **[Knowledge](knowledge/README.md)** | Organize evidence and distinguish trustworthy claims | [Source quality](knowledge/source-quality.md) |
| **[Memory](memory/README.md)** | Understand personalization, retention and privacy boundaries | [Memory lifecycle](memory/memory-lifecycle.md) |
| **[Context Engineering](context-engineering/README.md)** | Select relevant context and respect instruction priority | [Context selection](context-engineering/context-selection.md) |
| **[Intelligent UI](intelligent-ui/README.md)** | Choose readable, accessible and useful presentation formats | [Format selection](intelligent-ui/response-format-selection.md) |

---

## Use `/INTEL`

`/INTEL` is the project's **natural-language command convention**, not a native ChatGPT slash command, installed plugin or automatic connection to this repository.

**1. Configure.** Follow the [activation guide](guides/chatgpt-activation.md), apply the [activation instructions](prompts/activation-instructions.md) in a supported ChatGPT instruction surface, and provide actual read access to the repository.

**2. Start with a source check.** In the configured conversation, try:

```text
/INTEL HELP
/INTEL STATUS
/INTEL QUERY: Explain context engineering using repository sources.
/INTEL UI: Compare memory, knowledge and context engineering.
/INTEL REVIEW: Identify unsupported claims in this answer.
```

**3. Verify the result.** The assistant should identify which sources it could actually retrieve and distinguish facts from proposed designs. If source access is unavailable, it must say so. **No command prefix grants write permission.**

[Command reference](COMMANDS.md) · [Conversation examples](examples/intel-command-examples.md) · [Source access design](architecture/activation-and-source-resolution.md)

---

## Offline-first local text generators (G1.8)

The Python PROMPT, CONCEPT and DOCUMENT generators default to offline deterministic Markdown with no API key, paid model, or external connection. Local Ollama inference and the explicitly billable OpenAI API are optional. A native ChatGPT host adapter is not installed or implied.

```bash
python -m generators prompt --objective "Draft a checklist" --authorize-create
```

[Provider routing and permission boundaries](architecture/provider-routing.md)

---

## Windows launcher

Double-click [intel.cmd](intel.cmd) for the local ChatGPT Intelligence tunnel
menu, or run `./scripts/intel.ps1 -Action Start` in PowerShell 5.1.
[Windows launcher guide](architecture/windows-launcher.md).

---

## GIF & Motion generator (G3.1)

Generate deterministic JSON frame storyboards and real procedural animated
GIF89a files with verified frame count, per-frame timing and loop metadata.
No third-party dependencies, external model calls or video inference.
[Motion generator documentation](architecture/motion-generator.md).

---

## BRAND generator (G2.4)

Deterministic brand briefs, G2.3-compatible JSON identity tokens, and static
SVG geometric mark concepts with bounded inputs and exclusive local export.
These are unreviewed design proposals, not trademark-cleared identities.
[BRAND generator documentation](architecture/brand-generator.md).

---

## THEME generator (G2.3)

Generate deterministic light/dark JSON design tokens or CSS custom properties
with measured WCAG 2.2 color-pair audits. No complete browser accessibility
certification is implied.
[THEME generator documentation](architecture/theme-generator.md).

---

## DESIGN generator (G2.2)

Create deterministic UI/UX specifications and static, responsive HTML
prototype source with bounded components and exclusive verified export.
No browser or functional application integration is implied.
[DESIGN generator documentation](architecture/design-generator.md).

---

## ComfyUI local acceptance (G2.1.3)

A read-only ComfyUI preflight and opt-in single-image verifier are available
via `python -m scripts.verify_comfyui_live`. No model or ComfyUI installation
is automated. [Windows setup and live acceptance](architecture/comfyui-live-acceptance.md).

---

## Local semantic images (G2.1.2, opt-in)

An optional, locally installed ComfyUI checkpoint can render semantic images
through a fixed core-node workflow. This requires explicit local inference
authorization and is **not** enabled by the default tunnel profile. It never
uses a cloud/Partner API node or paid-model fallback. Live installation and
model execution remain user-environment acceptance gates.
[ComfyUI local setup](architecture/image-generator.md).

---

## IMAGE production briefs (G2.1)

The local `IMAGE` command and MCP tools create or validate editable Markdown
creative briefs, including image prompts, composition, palette and aspect ratio.
**They do not render image files.** [G2.1 specification](architecture/image-generator.md).

---

## ChatGPT client handoff (G1.9)

The local MCP stdio host accepts client-authored Markdown via three
`submit_*_draft` tools without an additional billable model API.
Connecting a real ChatGPT client requires an authorized custom MCP plugin
and Secure MCP Tunnel or remote endpoint; installation is not automatic.

[ChatGPT host integration setup](architecture/chatgpt-host-integration.md)

---

## Design principles

The reference architecture follows a simple sequence:

**User objective → Applicable instructions → Relevant context → Evidence and uncertainty → Answer structure → Appropriate UI → Review**

It is a **proposed interaction-design method**, not a description of ChatGPT's hidden internal processing.

| Principle | In practice |
| --- | --- |
| **Evidence before certainty** | Support changing product claims with relevant, dated sources |
| **Context with boundaries** | Use what is relevant and permitted; avoid unnecessary personal data |
| **Structure before decoration** | Select tables, visualizations or interactive elements only when useful |
| **Transparent limitations** | Distinguish verified capabilities, proposed designs and experiments |
| **Quality over complexity** | Prefer focused, understandable and maintainable workflows |

Go deeper: [Architecture Overview](architecture/overview.md) · [Response Lifecycle](architecture/response-lifecycle.md) · [ChatGPT Compatibility](architecture/chatgpt-compatibility.md) · [Evidence & Source Quality](knowledge/evidence-and-source-quality.md)

---

## Project status

**Documentation roadmap complete: 6/6 phases within their stated scopes.** The repository now follows a maintenance-oriented workflow.

| Delivered | Status |
| --- | --- |
| Foundation, architecture and seven domain guides | Complete within documentation scope |
| Prompt patterns, templates and examples | Complete within documentation scope |
| Evaluation framework and repository quality checks | Complete within framework scope |
| Editorial review and closeout record | Complete within scoped documentation review |
| Branding v1.4 | 57 original assets published and integrity-verified |

The distinction matters: **a complete documentation project is not a certified ChatGPT integration or software release.** Twelve fresh-chat `/INTEL` scenarios, live Intelligent UI behavior, comprehensive independent visual review and independent editorial/privacy approval remain **unverified and optional for future product certification**.

[Project Closeout](quality/project-closeout.md) · [Full Roadmap](ROADMAP.md) · [Release Readiness](quality/phase06-release-readiness.md) · [Branding](branding/README.md)

## Project resources

| Resource | Contents |
| --- | --- |
| [Architecture](architecture/overview.md) | Interaction models, decision logic and compatibility |
| [Guides](guides/README.md) | Getting started, activation and practical workflows |
| [Templates](templates/README.md) · [Examples](examples/README.md) | Reusable artifacts and worked scenarios |
| [Quality](quality/quality-standards.md) | Evaluation criteria, limitations and evidence records |
| [Brand assets](branding/README.md) | Light/dark banners, icons, wordmarks and [contact sheet](branding/v1.4/asset-contact-sheet.png) |
| [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) | Project history and contribution guidelines |

---

### Independent project and responsible use

ChatGPT Intelligence is **not affiliated with or endorsed by OpenAI**. ChatGPT is an OpenAI trademark; review the [OpenAI brand guidelines](https://openai.com/brand/) before using this name for a marketed product. These materials do not control model internals, modify native ChatGPT UI, synchronize Memory or guarantee response quality. Do not commit credentials, private conversations or personal memory exports.

<p align="center">
  <strong>Clarity in research. Precision in design. Evidence in every claim.</strong>
</p>
