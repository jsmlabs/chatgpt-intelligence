# ChatGPT Intelligence

> Research, concepts, prompts, knowledge, memory, context engineering, and intelligent UI principles for high-quality, personalized ChatGPT experiences.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="branding/v1.4/banners/readme-hero-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="branding/v1.4/banners/readme-hero-light.png">
  <img alt="ChatGPT Intelligence - Independent research and design" src="branding/v1.4/banners/readme-hero-light.png">
</picture>

**Understand ChatGPT. Design better interactions. Document what works.**

ChatGPT Intelligence is an open, beginner-friendly knowledge and documentation repository. It explores how to create clearer, more reliable, context-aware, and personalized ChatGPT experiences through research, design principles, reusable prompts, practical examples, and transparent evaluation.

**Documentation first:** This is not an installed plugin, an API service, an internal description of ChatGPT, or an automatic memory synchronization system.

## Start here

**Use inside ChatGPT:** [Try `/INTEL`](COMMANDS.md) to activate the repository-grounded conversation convention in an appropriately configured chat. Follow the [activation guide](guides/chatgpt-activation.md); a prefix alone does not connect GitHub or install an app.

New to the project? Read [Getting Started](GETTING_STARTED.md). It explains where to look and how to distinguish evidence from proposals. View the [Roadmap](ROADMAP.md) for milestones and current work. For immediately useful patterns, see the [Prompt Pattern Library](prompts/prompt-patterns.md) and [Intelligent UI Response Patterns](intelligent-ui/response-patterns.md).

## Explore the seven core areas

| Area | What you will find |
| --- | --- |
| [Research](research/README.md) | Investigations, sources, experiments, and product limitations |
| [Concepts](concepts/README.md) | Ideas, reference models, alternatives, and trade-offs |
| [Prompts](prompts/README.md) | Reusable instructions, prompt patterns, and clear output contracts |
| [Knowledge](knowledge/README.md) | Sources, reliable facts, uncertainty, and knowledge organization |
| [Memory](memory/README.md) | Memory concepts, personalization, consistency, and privacy |
| [Context Engineering](context-engineering/README.md) | Relevant information, instruction priority, and context selection |
| [Intelligent UI](intelligent-ui/README.md) | Response design, formatting, visualizations, and useful interactions |

## How the pieces fit together

Start with a user objective. Resolve applicable instructions, gather relevant and permitted context, verify time-sensitive claims, plan the answer's information structure, select useful presentation elements, and evaluate the result.

This is a **proposed design workflow**, not a statement about ChatGPT's hidden processing.

Read [Architecture Overview](architecture/overview.md), [Response Lifecycle](architecture/response-lifecycle.md), and [Intelligent UI Decision Model](architecture/intelligent-ui-decision-model.md).

## Documentation and standards

| Resource | Purpose |
| --- | --- |
| [Roadmap](ROADMAP.md) | Delivery phases, current state, and acceptance criteria |
| [Command Reference](COMMANDS.md) | Proposed `/INTEL` commands for ChatGPT |
| [Activation Guide](guides/chatgpt-activation.md) | Setup and source-verification workflow |
| [Branding](branding/README.md) | Published original v1.4 package, tokens, and integrity verification |
| [Branding Integration](guides/branding-integration.md) | Safe installer, import and hash verification |
| [Conversation Examples](examples/intel-command-examples.md) | Expected `/INTEL` user flows |
| [End-to-End Tests](quality/intel-end-to-end-tests.md) | Fresh-chat test cases and evidence rules |
| [INTEL Test Results](quality/intel-e2e-results.json) | Per-case evidence ledger, initially not-run |
| [INTEL Fresh-Chat Runbook](quality/intel-fresh-chat-runbook.md) | Reproducible twelve-case acceptance instructions |
| [Source Retrieval Smoke Test](quality/intel-source-smoke-test.md) | Existing-chat GitHub read-back results and limitations |
| [Pattern Evaluation](quality/pattern-evaluation.md) | Phase 05 scoring rubric and critical failures |
| [Local Verifier Execution](quality/local-verifier-execution.md) | Earlier scoped local tests and limitations |
| [Phase 05 Verification](quality/phase05-verification.md) | Verified CI and quality regression results |
| [Branding Publication Verification](quality/branding-publication-verification.md) | 57/57 exact original assets and 56/56 GitHub SHA-256 checks |
| [Branding Visual Inspection](quality/branding-visual-inspection.md) | Scoped contact-sheet and light-banner inspection, with remaining gaps |
| [Phase 06 Release Readiness](quality/phase06-release-readiness.md) | Initial release review and outstanding acceptance gates |
| [Release Gate Verification](quality/release-gate-verification.md) | Tested strict release readiness check and five blockers |
| [Strict Release Readiness Workflow](.github/workflows/release-readiness.yml) | Manual CI validation of release prerequisites without publishing a release |
| [Automated Quality Checks](.github/workflows/docs-quality.yml) | Documentation CI and regression tests |
| [Verifier Regression Tests](tests/test_quality_scripts.py) | Deterministic tests for link and archive verification |
| [Phase 04 Verification](quality/phase04-verification.md) | Scoped documentation checks and pending gates |
| [Architecture](architecture/overview.md) | How the project's concepts fit together |
| [Compatibility](architecture/chatgpt-compatibility.md) | Model, client, plan, evidence, and version boundaries |
| [Design Principles](architecture/design-principles.md) | Core project principles |
| [Guides](guides/README.md) | Accessible learning paths |
| [Templates](templates/README.md) | Reusable document structures |
| [Examples](examples/README.md) | Clear illustrations and comparisons |
| [Quality](quality/quality-standards.md) | Review and evaluation standards |
| [Foundation Verification](quality/foundation-verification.md) | Recorded baseline checks and their limits |
| [Architecture Verification](quality/architecture-verification.md) | Phase 02 verification record |
| [Knowledge Domain Verification](quality/knowledge-domain-verification.md) | Phase 03 verification record |
| [Contributing](CONTRIBUTING.md) | How to propose and document improvements |
| [Changelog](CHANGELOG.md) | Changes to this documentation |

## Evidence and compatibility

A changing ChatGPT feature is not considered verified just because it appears in this repository.

- `verified-capability`: supported by dated, applicable evidence.
- `proposed-design`: a recommended design, not a confirmed product behavior.
- `experimental`: an observation or hypothesis that needs further checking.

See [ChatGPT Compatibility](architecture/chatgpt-compatibility.md) for how to record scope, verification dates, sources, and limitations.

## What this repository does not do

`/INTEL` is a documented prompt convention, not a native ChatGPT command. The fully published v1.4 branding package is a visual identity, not an installed ChatGPT theme.

It does not control OpenAI model internals, override higher-priority instructions, synchronize ChatGPT Memory, guarantee response quality, or make every UI component available in every client.

Public contributions must not include secrets, private chat histories, or personal memory exports.

## Project status

**Phases 01-04 documented within their respective scopes; Phase 05 in progress, Phase 06 review started (release blocked).** All seven knowledge areas have practical guides, examples, limitations, and initial evaluation criteria. Verified GitHub Actions QA has passed (26 tests, 372 checked relative links); the strict release gate reports four incomplete conditions. Brand v1.4 is fully published and hash-verified; actual `/INTEL` activation tests, broader source-backed capability inventories, independent product checks, and formal evaluations remain future work.

[Get Started](GETTING_STARTED.md) | [Roadmap](ROADMAP.md) | [Contribute](CONTRIBUTING.md)
