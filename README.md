<picture>
  <source media="(prefers-color-scheme: dark)" srcset="branding/v1.4/banners/readme-hero-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="branding/v1.4/banners/readme-hero-light.png">
  <img src="branding/v1.4/banners/readme-hero-light.png" alt="ChatGPT Intelligence - Independent research and design" width="1600">
</picture>

# ChatGPT Intelligence

> Research, concepts, prompts, knowledge, memory, context engineering, and intelligent UI principles for high-quality, personalized ChatGPT experiences.

**Understand ChatGPT. Design better interactions. Document what works.**

An independent, open documentation and research library for creating clearer, more reliable, context-aware and visually effective ChatGPT experiences. It brings together **practical methods, reusable prompts, evidence standards, design patterns and implementation boundaries** in one navigable knowledge base.

**Documentation project · Seven core domains · Six documentation phases complete · Maintenance mode**

[**Get started**](GETTING_STARTED.md) · [**Explore the domains**](#explore-the-seven-core-areas) · [**Use /INTEL**](#use-intel-in-chatgpt) · [**Architecture**](architecture/overview.md) · [**Roadmap**](ROADMAP.md)

---

## Start here

| I want to... | Start with |
| --- | --- |
| Understand the project in five minutes | [Getting Started](GETTING_STARTED.md) |
| Use the documented `/INTEL` conversation workflow | [Activation Guide](guides/chatgpt-activation.md) and [Command Reference](COMMANDS.md) |
| Improve a prompt or reuse a response structure | [Prompt Pattern Library](prompts/prompt-patterns.md) |
| Understand memory, knowledge and context boundaries | [Context & Information Boundaries](architecture/context-and-information-boundaries.md) |
| Design readable answers, tables and interactive responses | [Intelligent UI Response Patterns](intelligent-ui/response-patterns.md) |
| Evaluate accuracy, evidence and limitations | [Quality Standards](quality/quality-standards.md) |

The material is written to be approachable without hiding technical trade-offs. Start with a domain below, then follow its practical articles and primary-source references.

## Explore the seven core areas

| Domain | Focus | Practical entry point |
| --- | --- | --- |
| **[Research](research/README.md)** | Questions, verification, experiments and uncertainty | [Research Method](research/research-method.md) |
| **[Concepts](concepts/README.md)** | Designing approaches, assessing alternatives and trade-offs | [Concept Development](concepts/concept-development.md) |
| **[Prompts](prompts/README.md)** | Instruction quality, reusable patterns and output contracts | [Prompt Design](prompts/prompt-design.md) |
| **[Knowledge](knowledge/README.md)** | Evidence, source quality and maintaining trustworthy information | [Source Quality](knowledge/source-quality.md) |
| **[Memory](memory/README.md)** | Personalization, remembered context, lifecycle and privacy | [Memory Lifecycle](memory/memory-lifecycle.md) |
| **[Context Engineering](context-engineering/README.md)** | Selecting relevant information and respecting instruction boundaries | [Context Selection](context-engineering/context-selection.md) |
| **[Intelligent UI](intelligent-ui/README.md)** | Content-first presentation, visualizations and useful interactions | [Response Format Selection](intelligent-ui/response-format-selection.md) |

Each area has its own overview, applied guidance and explicit limitations. **Proposed design principles are not automatically verified ChatGPT product features.**

---

## Use `/INTEL` in ChatGPT

`/INTEL` is a **documented natural-language command convention** for repository-grounded conversations, not a built-in ChatGPT slash command or an installed plugin.

In a ChatGPT conversation with the [activation instructions](prompts/activation-instructions.md) **and** actual access to this repository, try:

```text
/INTEL HELP
/INTEL STATUS
/INTEL QUERY: Explain context engineering with repository sources.
/INTEL UI: Compare memory, knowledge and context engineering.
/INTEL REVIEW: Check this answer for unsupported claims.
```

| Command | Purpose |
| --- | --- |
| `/INTEL HELP` | Available commands and setup requirements |
| `/INTEL STATUS` | Observed source access and revision, not assumed activation |
| `/INTEL QUERY` or `SOURCE` | Source-grounded answers and file inspection |
| `/INTEL RESEARCH` or `DESIGN` | Evidence review or design exploration |
| `/INTEL UI` or `REVIEW` | Purposeful presentation or quality assessment |

**Setup:** [Connect a readable source and apply the activation instructions](guides/chatgpt-activation.md). Without source access, answers must disclose that limitation instead of inventing GitHub retrieval. Commands are read-only unless a separate, specific write is authorized.

[Full command reference](COMMANDS.md) · [Conversation examples](examples/intel-command-examples.md) · [Source-resolution design](architecture/activation-and-source-resolution.md)

---

## From question to high-quality answer

This repository recommends a transparent, **proposed** decision workflow:

```text
User objective
    |
    v
Applicable instructions and permissions
    |
    v
Relevant context and trustworthy sources
    |
    v
Evidence, uncertainty and constraints
    |
    v
Answer structure and appropriate UI
    |
    v
Verification, limitations and next action
```

This is a **design framework**, not a claim about ChatGPT's hidden internal processing. See the [Architecture Overview](architecture/overview.md), [Response Lifecycle](architecture/response-lifecycle.md) and [Intelligent UI Decision Model](architecture/intelligent-ui-decision-model.md).

### Evidence over assumptions

| Classification | Interpretation |
| --- | --- |
| `verified-capability` | Supported by a dated, applicable source or reproducible observation |
| `proposed-design` | A recommended pattern or architecture, not confirmed product behavior |
| `experimental` | A tentative observation requiring further evaluation |

Consult [ChatGPT Compatibility](architecture/chatgpt-compatibility.md) and [Evidence & Source Quality](knowledge/evidence-and-source-quality.md) before generalizing product behavior across models, plans or clients.

---

## Project status

**Documentation roadmap: 6/6 phases complete within their defined scopes.** The repository is in **maintenance mode**, with a preserved quality framework and published branding.

| Delivered | Current state |
| --- | --- |
| Foundation and core architecture | Complete within documentation scope |
| Seven knowledge domains | Complete within documentation scope |
| Reusable patterns and examples | Complete within documentation scope |
| Quality framework and repository checks | Complete within evaluation-framework scope |
| Editorial review and project closeout | Complete within scoped review; formal release deferred |
| Original branding v1.4 | **57 original files published**, with verified manifest integrity |

**Separate, optional future certification:** The 12 fresh-chat `/INTEL` scenarios, live Intelligent UI behavior, full independent visual/accessibility approval and independent editorial/privacy review are **not certified**. The [strict release gate](quality/phase06-release-readiness.md) preserves those conditions; a closed documentation roadmap is not a tagged software release.

[Project Closeout](quality/project-closeout.md) · [Roadmap](ROADMAP.md) · [Quality & Evaluation](quality/phase05-verification.md) · [Branding Verification](quality/branding-publication-verification.md)

---

## Repository guide

| Area | What's inside |
| --- | --- |
| [`architecture/`](architecture/overview.md) | Reference models, design principles and compatibility boundaries |
| [`guides/`](guides/README.md) | Onboarding, activation and practical workflows |
| [`prompts/`](prompts/README.md) | Prompt techniques, patterns and activation instructions |
| [`templates/`](templates/README.md) and [`examples/`](examples/README.md) | Reusable structures and worked illustrations |
| [`quality/`](quality/quality-standards.md) | Evaluation methods, evidence records and scope limitations |
| [`branding/`](branding/README.md) | Light/dark identity, artwork, tokens and static preview |

The [v1.4 brand package](branding/README.md) includes original light/dark banners, icons, wordmarks and an [asset contact sheet](branding/v1.4/asset-contact-sheet.png). The visuals identify this independent project; they do not skin or modify the native ChatGPT interface.

## Contributing and project boundaries

Corrections, current primary sources, useful examples and focused documentation improvements are welcome. Start with [Contributing](CONTRIBUTING.md), follow the [documentation contracts](architecture/documentation-contracts.md), and review the [Changelog](CHANGELOG.md).

This project is **not affiliated with or endorsed by OpenAI**. `ChatGPT` is an OpenAI trademark. Product naming and promotional use require appropriate [brand-guideline review](https://openai.com/brand/). The repository does not control models, alter ChatGPT Memory, guarantee output quality or provide a native plugin. **Never commit credentials, personal chat histories or sensitive memory exports.**

---

<p align="center">
  <strong>Clarity in research. Precision in design. Evidence in every claim.</strong>
</p>

<p align="center">
  <a href="GETTING_STARTED.md">Get started</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="quality/project-closeout.md">Project closeout</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>
