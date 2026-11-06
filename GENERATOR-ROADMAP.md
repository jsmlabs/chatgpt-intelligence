---
title: INTEL Generator Ecosystem Roadmap
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# /INTEL Generator Ecosystem - Product Roadmap

> Extend the existing research and documentation reference project with a modular, evidence-aware workflow for generating, validating, revising, and exporting useful artifacts.

**Status:** Active staged implementation. G0 contracts, G1 text generators, G1.8 local provider routing and G1.9 ChatGPT-client MCP handoff have been implemented. G2.1 provides an IMAGE *production-brief generator* only, not bitmap rendering. All other creative capabilities and external exports remain planned until individually verified. The original release gates remain in force.

## Verified implementation matrix (2026-11-06)

| Capability | Actual implemented scope | Native output produced? |
| --- | --- | --- |
| PROMPT / CONCEPT / DOCUMENT | Deterministic Markdown; optional local Ollama; client-supplied Markdown via MCP | Markdown drafts only |
| IMAGE (G2.1) | Deterministic image production briefs, creative prompts and client-authored brief intake | **Procedural abstract PNG available; optional local ComfyUI semantic adapter implemented, not live-verified** |
| DESIGN / THEME / BRAND | Registered but planned | No |
| GIF / SLIDES / DIAGRAM / CHART / CODE | Registered but planned | No |
| VIDEO / AUDIO / WORKFLOW / PACK | Registered but planned | No |

The G1.9 technical ChatGPT handoff has been observed through real client tool calls (three reviewed responses). Origin is not independently attested, and this observation does not certify full security, content quality or release readiness.

## 1. Vision and scope

**Product vision:** Make `/INTEL` an integrated intelligence and creative-workflow convention: from a researched brief through a structured concept and production-ready deliverable, with clear source provenance, editable intermediate artifacts, appropriate rendering, verification, and export.

**Primary audience:** Researchers, creators, designers, software engineers, product builders, and knowledge workers.

**Preserve existing work:** The original [documentation roadmap](ROADMAP.md) remains closed within its stated scope. The seven knowledge domains (research, concepts, prompts, knowledge, memory, context engineering, intelligent UI), existing brand assets, tests, and command documentation remain canonical. This roadmap opens a separate product-expansion track; it does not certify or reopen the original phases.

**Non-goals for the first release:** Native modification of ChatGPT internals; unconditional access to image/video/GIF generation tools; unsupervised publishing; autonomous payments or deployment; automatic synchronization of user memory; unrestricted use of copyrighted or private source material; support for every artifact format.

## 2. Capability catalog and priority

Priorities: **P0 = initial usable MVP**, **P1 = creative production**, **P2 = richer media**, **P3 = advanced workflows**. Capability labels describe product goals, not necessarily installed renderers. See the verified implementation matrix below.

| Capability | Proposed command | Core output | Priority |
| --- | --- | --- | --- |
| Prompt Generator | `/INTEL GENERATE PROMPT` | Reusable prompt, variables, constraints, evaluation cases | P0 |
| Concept Generator | `/INTEL GENERATE CONCEPT` | Concept brief, alternatives, trade-offs, acceptance criteria | P0 |
| Document Generator | `/INTEL GENERATE DOCUMENT` | Structured reports, PRDs, technical docs, optional supported export | P0 |
| Image Generator | `/INTEL GENERATE IMAGE` | Art direction, image prompt, generated/edited image if tool available | P1 |
| Design Generator | `/INTEL GENERATE DESIGN` | UI/UX brief, component spec, mockup or prototype if supported | P1 |
| Theme Generator | `/INTEL GENERATE THEME` | Palette, typography, accessible design tokens, light/dark variants | P1 |
| Brand Generator | `/INTEL GENERATE BRAND` | Identity guidelines, logo directions, brand asset brief | P1 |
| GIF & Motion Generator | `/INTEL GENERATE GIF` | Storyboard, frames, animation and GIF export when available | P2 |
| Slide Generator | `/INTEL GENERATE SLIDES` | Presentation narrative, slide structure and supported slide export | P2 |
| Diagram Generator | `/INTEL GENERATE DIAGRAM` | Mermaid/SVG/diagram source and accessible description | P2 |
| Chart & Data Generator | `/INTEL GENERATE CHART` | Traceable data transformation, chart and methodology | P2 |
| Code & Prototype Generator | `/INTEL GENERATE CODE` | Spec-based code, tests, review and runnable artifact if supported | P2 |
| Video Generator | `/INTEL GENERATE VIDEO` | Shot list, storyboard and video artifact when authorized tools exist | P3 |
| Audio Generator | `/INTEL GENERATE AUDIO` | Script, timing and audio where rights and tools permit | P3 |
| Workflow Generator | `/INTEL GENERATE WORKFLOW` | Multi-step plan with dependencies, validation and approval gates | P3 |
| Template & Asset Pack Generator | `/INTEL GENERATE PACK` | Consistent multi-format deliverable manifest | P3 |

The catalog is expandable through a reviewed capability registry; do not implement each generator as a separate, incompatible orchestration stack.

## 3. Phased delivery

### G0 - Contract and feasibility (first)
**Deliverables**
- Registry schema and lifecycle: capabilities, inputs, output MIME types, constraints, permissions, available adapters, and fallbacks.
- User-facing command grammar; canonical existing commands remain valid.
- Tool-availability matrix distinguishing **documented**, **available in the current session**, **tested**, and **unsupported**.
- Artifact manifest with source paths, version, producer, output type, verification status and limitations.
- First release decisions on host environment, storage/export strategy and naming/trademark review.

**Acceptance:** Unknown commands fail safely; a command cannot claim a missing generation or export capability; existing `/INTEL QUERY`, `RESEARCH`, `DESIGN`, `UI`, `REVIEW`, and `SOURCE` retain their meaning. Security rules and format contract are reviewed before building adapters.

### G1 - Text-first MVP (P0)
**Deliverables**
- Prompt, Concept and Document Generators.
- Shared `brief -> generate -> review -> revise -> export` workflow.
- Structured templates, provenance/assumptions, explicit artifact version and editable outputs.
- Preview and Markdown export by default; DOCX/PDF export only when an actual supported tool is connected.
- Demonstrations and deterministic validation fixtures.

**Acceptance:** Each generator passes at least three realistic golden-case fixtures, one missing-input case, one untrusted-input case, one revision case and one unsupported-export case. No invented citations or file links. Every accepted artifact can be edited without losing its intent or revision history.

### G2 - Visual design & brand (P1)
**Deliverables**
- Image, Design, Theme and Brand Generators.
- Reusable visual brief, asset/style consistency rules, accessibility and responsive design checks.
- Optional image-generation and product-design adapters with graceful fallback to prompts/specifications.
- Review UI allowing comparison of alternatives and selection of a revision target.

**Acceptance:** Generated design tokens follow a documented schema; contrast checks report results rather than assuming pass; image/model/tool provenance is recorded; exports are verified on disk or through the provider before linking.

### G3 - Motion & structured media (P2)
**Deliverables**
- GIF/motion, slides, diagrams, chart/data and code/prototype generators.
- Asset dependency graph, frame/timing specifications, visual/semantic previews, format-aware export.
- Data validation and traceability for quantitative outputs; reproducibility for deterministic transformations.

**Acceptance:** At least one tested export per implemented generator; frame count/timing, slide contents, diagram source, chart data origin and code tests are inspected as relevant. If runtime media tools are absent, generate a storyboard/specification and label it accordingly - not a completed GIF/video.

### G4 - Advanced production (P3)
**Deliverables**
- Video/audio, workflow and multi-asset pack orchestration.
- Explicit external-action approvals; bounded resource and cost budgets; selective provider integrations.
- Pluggable publication/deployment targets only when authorized and available.

**Acceptance:** A dry-run manifest shows all intended side effects; publishing/deploying requires separate authorization; partial failure leaves usable artifacts and machine-readable failure records.

### G5 - Beta certification and release (separate gate)
**Deliverables**
- Verified end-to-end target-client scenarios; accessibility, privacy, legal/trademark and security review; release notes and rollback strategy.
- Real environment checks covering unavailable tools, corrupted assets, unsupported formats and user-provided untrusted text.

**Acceptance:** Tests are executed, not merely written; critical findings are resolved; verification evidence and revision identifiers are published. No release/tag without explicit authorization and passed gates.

## 4. Command grammar

Proposed canonical form:

```text
/INTEL GENERATE <TYPE>
Goal: <intended result>
Audience: <target audience>
Inputs: <sources or files>
Style: <tone or visual direction>
Format: <preferred output, subject to available tools>
Constraints: <requirements, exclusions, budget>
Verification: <what must be checked>
```

Examples:

```text
/INTEL GENERATE PROMPT
Goal: Write a secure, reusable agent prompt for repository code reviews.
Format: Markdown
Verification: Include tool boundaries, failure behavior, acceptance tests.
```

```text
/INTEL GENERATE THEME
Goal: Design an accessible dark/light theme for a dashboard.
Inputs: Existing brand tokens if accessible.
Format: CSS custom properties + token JSON
Verification: Check contrast and token completeness.
```

```text
/INTEL GENERATE GIF
Goal: A three-second looping product loading animation.
Style: Minimal geometric motion.
Format: GIF if a suitable renderer is available; otherwise storyboard.
Verification: Inspect frame sequence, loop and exported file.
```

**Compatibility rule:** Existing `/INTEL DESIGN` remains the research/design-analysis command; `/INTEL GENERATE DESIGN` explicitly requests an artifact. `/INTEL HELP` must only advertise what is implemented, and can separately display planned commands. Merely typing a command does not grant repository write, file export, publishing or external-tool permission.

## 5. Proposed architecture

```text
User request / source artifacts
          |
Command parser + capability registry
          |
Scope & permission gate ------ Tool availability discovery
          |                             |
Brief/intent schema <------ Adapter capability matrix
          |
Plan + artifact manifest
          |
Generator adapter (text / image / design / document / motion / ...)
          |
Format-specific validation and review
          |
Preview / revision / export adapter
          |
Verified artifact + evidence + limitations
```

**Core contracts**
- **Capability:** `id`, `command`, `input_schema`, `outputs`, `required_tools`, `fallback`, `risk_class`.
- **Request:** `goal`, `audience`, `inputs`, `style`, `format`, `constraints`, `verification`.
- **Artifact:** `id`, `type`, `version`, `content_or_ref`, `source_refs`, `generator`, `status`, `checks`.
- **Execution states:** `planned -> ready -> generating -> validating -> reviewed -> exported`, plus explicit `blocked` / `failed` states. Do not transition to `exported` before output existence is verified.
- **Boundaries:** Generative output does not authorize actions. A deterministic policy/permission layer decides whether each adapter may read, write, publish, charge or invoke external services.

Provider adapters are optional and environment-specific. Prefer reusing supported host capabilities to constructing proprietary rendering or model APIs for the first MVP.

## 6. Quality, safety, accessibility and provenance

1. **Grounding:** Track original versus derived content, sources, dates, tool/model identity when available, and uncertain claims. Never fabricate a generated file.
2. **Security:** Treat source documents, URLs and generated content as untrusted. Enforce bounded execution, path safety, permission checks and no credential leakage.
3. **Privacy:** Keep personal/connected data out of public repos and sample fixtures; prefer synthetic examples.
4. **Rights:** Require lawful use of supplied media; do not silently reproduce protected branding or copyrighted works.
5. **Accessibility:** Include alt text, legible type, contrast testing and reduced-motion alternatives as applicable.
6. **Revisions:** Preserve editable source, user constraints and version lineage; do not destructively replace originals without permission.
7. **Validation:** Separate automated structural tests, human review and runtime/client acceptance. State `passed`, `failed`, `blocked`, or `not run` precisely.
8. **Brand/legal:** The project is independent of OpenAI; a marketed product name and branding must undergo trademark review before commercialization.

## 7. Suggested repository ownership

Re-use existing domains for explanatory guidance:
- `prompts/`: prompt patterns and prompt generation guidance.
- `concepts/`: concept development and decision methods.
- `intelligent-ui/`: presentation, previews and interface design criteria.
- `branding/`: existing asset identity and future style guidance.
- `quality/`: validation rules, test cases and evidence.

**Only when implementation begins**, propose a `generators/` package with the shared registry, schemas, adapters and tests. Do not create empty folders or duplicate the canonical documents in this planning phase.

## 8. Dependencies and decisions

| Decision | Default proposal | Why it matters |
| --- | --- | --- |
| First runtime | ChatGPT-hosted workflows where available | Validates actual capabilities before building infrastructure |
| MVP generators | Prompt, Concept, Document | Text-first outputs share contracts and have low media dependencies |
| Next wave | Image, Design, Theme, Brand | Reuses the same brief, approval and revision contract |
| Motion engine | Adapter chosen after feasibility test | GIF/video support differs across host environments |
| Export | Markdown first, verified additional files later | Avoids imaginary download links |
| Persistence | Versioned manifests; no automatic memory writes | Auditable and least privilege |
| Monetization | Out of scope | Keep first delivery focused on practical utility |
| Product naming | Provisional until legal review | Existing trademark risk is documented in the original release review |

**Open questions:** Which hosting/integration environment should own dispatch and persistence? Which providers are permitted for raster images, animation and document export? Should artifacts remain chat-scoped or be stored in a dedicated user workspace? These decisions belong in G0 and must be evidence-backed.

## 9. Immediate actionable backlog

1. Specify the capability registry and typed artifact/request contracts.
2. Document compatibility and help-discovery behavior for old and proposed commands.
3. Build and verify a Prompt Generator using shared schemas.
4. Add Concept Generator using the same review/revision workflow.
5. Add Document Generator with Markdown export and optional tested file adapters.
6. Define golden cases, adversarial input tests and export verification.
7. Run a G1 MVP acceptance review, then select the first visual adapter based on real tool availability.

## 10. Status and release policy

**Planning status:** Proposed; not implemented or client-tested as a product. No existing formal-release blockers are silently waived. A GitHub documentation commit proves publication of this proposal only, not generator functionality.

[Current command reference](COMMANDS.md) | [Original roadmap](ROADMAP.md) | [Architecture](architecture/overview.md) | [Quality standards](quality/quality-standards.md)


## G0 implementation status (2026-11-06)

The `generators/` Python reference runtime now implements deterministic parsing, the 16-entry planned registry, deny-by-default permission/tool contracts, and guarded artifact state transitions. **No creative generator, real provider adapter, native ChatGPT slash command, persistent artifact writer or external integration is available.** `/INTEL GENERATE <TYPE>` returns `CAPABILITY_UNAVAILABLE` for planned generators; legacy interactive operations still require a host integration. See [architecture](architecture/generator-foundation.md) and [tests](tests/test_generators.py). The original documentation project and its seven domains are unchanged. This implementation is not certification of G1.

## G1 implementation checkpoint (2026-11-06)

A local Python text-first runtime has been added for `PROMPT`, `CONCEPT`, and `DOCUMENT` with deterministic templates, request validation, explicit local creation permission, reviewed draft manifests, revisions and verified Markdown export. All other generators remain planned. This is a **local reference MVP**, not a model-backed ChatGPT native integration. Source verification and human editorial review remain not run. See [runtime architecture](architecture/text-runtime.md) and [G1 tests](tests/test_text_runtime.py). G1 external-tool and client acceptance criteria are **not yet certified**.

## G1.6 implementation checkpoint (2026-11-06)

An opt-in Python Responses API host adapter and injectable model-host contract have been added for the three G1 text generators. External and billable permissions are checked before execution; the original registry, G0 dispatcher and artifact lifecycle are unchanged. Synthetic transport tests are not evidence of live provider access. Current status: **integration code implemented; live provider/client verification not run**. See [model-host architecture](architecture/model-host.md).

## G1.7 checkpoint (2026-11-06)

A local MCP stdio host with three bounded text tools, explicit startup grants and isolated synthetic protocol tests has been implemented. The live-provider verifier `scripts/verify_model_live.py` requires environment-provided credentials plus explicit billable authorization and is intentionally excluded from CI. **Local MCP support is not native ChatGPT plugin installation.** A real authenticated model call and ChatGPT-client acceptance must be verified separately; no release gate is waived. [Integration guide](architecture/mcp-host.md).
## G1.7 model-hardening checkpoint (2026-11-06)

Following a user-reported three-generator live `PASSED` on the preceding revision, model defaults and diagnostic categories were hardened with regression coverage. The preceding live result is external, user-supplied evidence; it does not prove that the hardened head passes live, or that a native ChatGPT client connected. Exact-head CI plus a subsequent separately authorized live run are required before claiming completion.

## G1.8.2 evidence and G1.9 boundary (2026-11-06)

A user-provided local Windows PowerShell transcript confirms a `gemma3:4b`
`ollama-local` CONCEPT generation on commit
`7a93a81ad5ebbea007f5f5c00c94399f33c0abcf`, with `llm_generation:
host_reported` and `structural_validation: passed`. The output had an
open outer `markdown` fence; the G1.8.2 change repairs or rejects
such wrappers deterministically. This is reported external acceptance evidence,
not a fresh live run against G1.8.2. Local PROMPT and DOCUMENT live runs remain
unverified. A separate proposed [G1.9 ChatGPT-host feasibility milestone]
(architecture/chatgpt-host-integration.md) must prove actual client support
before `chatgpt-host` is marked operational.

## G1.9 MCP host-handoff implementation checkpoint (2026-11-06)

Three additive MCP `submit_*_draft` tools accept client-authored Markdown,
apply G0 permission and artifact contracts and return structurally reviewed
in-memory content. Their provenance is not independently attested.
The local stdio verifier exercises the transport without an external model
or paid provider. Actual ChatGPT-client connectivity was subsequently exercised in the
current development conversation: three client-initiated `submit_*_draft`
calls returned `reviewed` and `structural_validation: passed`.
This is technical handoff acceptance, not independent model-origin
attestation or production release approval. See
[G1.9 integration](architecture/chatgpt-host-integration.md).

## G2.1 IMAGE production-brief checkpoint (2026-11-06)

The `IMAGE` capability is now available **only for Markdown image
production briefs** through the Python CLI and two add-on MCP tools:
`generate_image_brief` and `submit_image_brief`. Briefs include aspect
ratio, audience, style, palette, composition, image prompt, alternatives,
constraints, provenance and review steps. Client-authored content is
validated and explicitly labeled `not-attested`.

The implementation uses the G0 create permission, existing artifact lifecycle,
structural Markdown checks and verified exclusive Markdown export. It performs
no raster rendering, model API request, or file download; `--format png` and
non-template model selections fail closed. The first G2.1 checkpoint is
**implemented for briefs**, while the original G2 deliverable of real image
generation remains **blocked pending a verified image-capable host adapter**.
See [G2.1 specification](architecture/image-generator.md).

## G2.1.1 - Local raster image adapter

A bounded procedural geometric PNG renderer is implemented as an opt-in local CLI
and additive MCP image-content tool. It outputs real CRC-checked PNG bytes,
without a model API or cloud provider. This does not satisfy the broader
requirement for natural-language semantic image generation; a verified AI
image provider adapter is a separate open milestone.

## G2.1.2 - Optional local semantic image adapter (2026-11-06)

A dependency-free Python client for locally installed ComfyUI runs a fixed
core-node text-to-image workflow against loopback, with explicitly authorized
local inference. It validates the checkpoint list and generated PNG, and
supports exclusive local export. The additive MCP tool is advertised **only**
when the operator starts the process with `--allow-comfyui-image`; the default
nine-tool local MCP host and non-billable routing remain unchanged. Neither
Ollama text models nor a ChatGPT subscription imply a ComfyUI checkpoint.

**Verification boundary:** Synthetic ComfyUI protocol, permission, image and
export tests are automated. No ComfyUI installation, model load, actual
semantic generation or native ChatGPT tool call has been observed on the
operator's Windows computer. The separate image-model live acceptance and
editorial/rights checks remain open. [Spec](architecture/image-generator.md).

## G2.1.3 - Local acceptance workflow (2026-11-06)

A read-only ComfyUI checkpoint probe and explicitly authorized single-image
acceptance verifier were added. The verifier reports READY, PASSED or BLOCKED,
checks actual PNG integrity and exclusive local export, and does not invoke
paid model APIs or install software. **No real ComfyUI model execution on the
operator's PC has been observed.** The [Windows acceptance checklist]
(architecture/comfyui-live-acceptance.md) documents installation prerequisites,
operator verification and optional ChatGPT MCP activation.
