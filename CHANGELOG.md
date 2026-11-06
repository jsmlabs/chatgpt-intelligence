# Changelog

This file records meaningful documentation changes. A proposed design or documentation revision does not imply an implementation or a published software release.

## Unreleased
### Added
- Added [G2.1.2 explicit local ComfyUI image generation](architecture/image-generator.md), a fixed core-node workflow with checkpoint and PNG verification, optional CLI export, and opt-in MCP image tool. Live ComfyUI generation remains unverified.
- Added G2.1.1 bounded, dependency-free procedural abstract PNG rendering with verified local file export and the `render_abstract_image` MCP image tool; no semantic AI image generation is claimed.
- Implemented [G2.1 IMAGE production briefs](architecture/image-generator.md) through the Python CLI and two additive MCP tools, with explicit `image_generated: false` provenance; real raster rendering remains a separate verified-adapter milestone.
- Consolidated [G1.9 technical handoff acceptance](architecture/chatgpt-host-integration.md) using three directly observed ChatGPT MCP results and preserving independent release/security gates.
- Windows launcher can now load the restricted tunnel runtime key from the user's Desktop/tunnel-client/key.txt (single-line, never printed), with masked prompt fallback and non-persistent process environment.
- Added [Windows INTEL launcher](architecture/windows-launcher.md) with one-click menu for foreground tunnel startup, status, diagnosis, MCP smoke test and optional Ollama listing, without stored credentials.
- [Closed all six documentation roadmap phases at explicitly limited scope](quality/project-closeout.md); marked the repository as maintenance-oriented without falsely completing fresh-chat tests, independent reviews or a formal release. Existing strict release checks remain unchanged.
- Hardened [branding media checks](scripts/check_brand_media.py) to reject external/executable HTML references and SVG event handlers or external resource references; four negative regression cases added. [GitHub Actions run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42231231309) passed 65 tests and checked 52 original brand media files.
- Ran a [scoped Chromium preview interaction smoke test](quality/branding-browser-smoke-test.md) on desktop and mobile, checking theme changes, sidebar response, horizontal overflow and JS runtime errors. The runtime blocked direct page navigation, so this is not a full resource-loading or accessibility audit.
- Added [brand media format validator](scripts/check_brand_media.py) with PNG CRC, SVG parsing and paired dimensions, plus seven regression cases and CI steps. [Verified GitHub Actions run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42223107435) passed 61 tests and 52 brand media checks. [Accessibility sampling](quality/branding-accessibility-sampling.md) records theme contrast values and a conditional light-accent caution, without asserting WCAG conformance.
- [Scoped editorial and primary-source review](quality/editorial-source-review.md) documents confirmed boundaries for `/INTEL`, Intelligent UI and Memory, plus an unresolved naming/trademark assessment before product promotion. This is not the independent review required for release.
- Hardened extracted branding verification against symlink aliases and malformed/noncanonical manifest entries; extended documentation checks to Markdown image links and HTML `src`/`srcset` assets. [CI run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42215683862): 54 passing tests, 427 checked file/image references with no errors.
- Strengthened [brand manifest verification](scripts/verify_branding.py) with strict exact-file mode, used by both release checking and documentation CI. Strengthened all release attestation evidence references, added regression tests, and introduced a [bounded tracked-text credential scan](scripts/check_publication_safety.py). [Latest verified run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42210670991): 46 tests, 410 links, 56/56 hashes, 111 scanned text files, zero high-confidence findings.
- Hardened [INTEL E2E validation](scripts/verify_intel_e2e.py) with ISO dates, full commit SHAs, existing local evidence files or HTTPS references, and integration tests for strict release enforcement. [Verified GitHub Actions run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42209415341) passed 33 tests.
- Added [fresh-chat acceptance runbook](quality/intel-fresh-chat-runbook.md) with exact prompts for all twelve E2E cases, plus a [scoped branding visual inspection](quality/branding-visual-inspection.md). Preserved the immutable original brand package and clarified its historical publication note in the parent branding index.
- Added [per-case `/INTEL` evidence validator](scripts/verify_intel_e2e.py) and [twelve initially not-run case records](quality/intel-e2e-results.json); strict release checker requires them if fresh-chat attestation is marked passed. [CI run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42208022435) passed 26 tests.
- Published all 57 original branding v1.4 files on `main`; [verified Git blob integrity](quality/branding-publication-verification.md) for 57/57 and manifest SHA-256 for 56/56 in GitHub Actions. Removed an unrelated newline-only placeholder; release blockers reduced from five to four.
- Added a [manually triggered strict release-readiness workflow](.github/workflows/release-readiness.yml); routine documentation CI remains non-blocking while five release prerequisites are missing.
- [Fail-closed release gate](scripts/check_release.py), [release evidence ledger](quality/release-evidence.json), five regression tests and [verified CI report](quality/release-gate-verification.md). CI passed 21 tests and confirmed five release blockers.
- Hardened ZIP verifier and installer against noncanonical paths and case-insensitive collisions. Four regression tests added; [16-test GitHub Actions run](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42205753806) passed.
- [Initial Phase 06 release-readiness review](quality/phase06-release-readiness.md) identifies verified CI evidence and outstanding branding, fresh-chat and runtime acceptance gates.
- [Phase 05 verification record](quality/phase05-verification.md): GitHub Actions run #21 passed 12 regression tests and checked 330 links across 57 Markdown files; isolated brand import passed 56/56 hash checks. Remote branding remains unpublished.
- Safe [branding v1.4 installer](scripts/install_branding.py) with preflight manifest checks, overwrite refusal, and rollback attempt; four installer regression tests added, execution pending.
- [Local verifier execution record](quality/local-verifier-execution.md): eight tests passed in a reconstructed environment, original brand ZIP verified, exact GitHub CI still unverified.
- Eight regression tests for documentation and brand archive verification in [tests/test_quality_scripts.py](tests/test_quality_scripts.py), wired into the CI workflow; execution status pending.
- Dependency-free [Markdown link/metadata checker](scripts/check_docs.py) and [documentation quality CI workflow](.github/workflows/docs-quality.yml); execution result pending verification.
- [Safe branding archive verifier](scripts/verify_branding_archive.py) for manifest SHA-256, ZIP CRC, traversal, duplicates, and size-limit checks.
- [INTEL source retrieval smoke test](quality/intel-source-smoke-test.md), confirming five canonical documents were actually fetched in an existing connected ChatGPT conversation, without claiming fresh-chat prefix activation.
- Phase 04: [prompt patterns](prompts/prompt-patterns.md), [Intelligent UI response patterns](intelligent-ui/response-patterns.md), [INTEL conversation examples](examples/intel-command-examples.md), and [response pattern template](templates/response-pattern-template.md).
- [INTEL end-to-end test plan](quality/intel-end-to-end-tests.md) and [branding installation guide](guides/branding-integration.md).
- [Brand manifest verification script](scripts/verify_branding.py) for exact local SHA-256 checks.
- [Phase 04 Verification Record](quality/phase04-verification.md) and [Phase 05 evaluation rubric](quality/pattern-evaluation.md).
- Documented the proposed [ChatGPT `/INTEL` activation convention](COMMANDS.md), source-resolution boundaries, setup guide, and paste-ready activation instructions.
- Integrated [brand v1.4 guidance](branding/BRAND-GUIDELINES.md), [tokens](branding/design-system/tokens.json), [CSS variables](branding/design-system/theme-tokens.css), and explicit binary-publication status.
- Expanded seven Phase 03 domain articles with practical workflows, examples, decision checklists, limitations, and evaluation exercises.
- [Phase 03 Verification Record](quality/knowledge-domain-verification.md) documenting reviewed scope and remaining validation limits.
- Phase 03 initial practical guides in all seven core domains, linked from their topic entry pages.
- Roadmap progress tracking for the seven-domain expansion.

- [Project Roadmap](ROADMAP.md) covering six documentation phases and acceptance criteria.
- [Foundation Verification Record](quality/foundation-verification.md) for the scoped 21-file baseline audit.
- [Architecture Verification Record](quality/architecture-verification.md) for the Phase 02 documentation checks.
- Phase 02 specifications for [instruction conflicts](architecture/instruction-and-conflict-resolution.md), [information boundaries](architecture/context-and-information-boundaries.md), [Intelligent UI selection](architecture/intelligent-ui-decision-model.md), and [documentation contracts](architecture/documentation-contracts.md).
- Beginner-friendly documentation foundation with seven core topic guides, templates, examples, and quality standards.
- Version-aware compatibility guidance distinguishing verified product capabilities, proposed designs, and experimental observations.

### Changed
- Refined the [root README](README.md) into a leaner, task-first landing page with the existing responsive light/dark hero, seven domain entry points, honest `/INTEL` setup, compact design principles, scoped project closeout and clearer resource navigation; no branding assets or capabilities changed.
- Redesigned the root [README](README.md) as a branded, task-oriented landing page: light/dark hero, seven domain entry points, accurate `/INTEL` setup, concise roadmap closeout, evidence boundaries and clearer contribution navigation. No product-release or client-certification claims were added.
- Prepared a collision-safe original brand archive layout in `branding/v1.4/`, preserving all 56 original assets and the manifest without replacing independently authored branding guides.
- Recorded binary branding publication and fresh-chat activation as open verification gates, rather than completed integrations.
- Advanced Phase 04 to completed documentation scope; Phase 05 evaluation remains pending.
- Clarified that the repository supports an opt-in ChatGPT usage convention, not an automatically registered slash command or native theme.
- Aligned Phase 03 roadmap status and README navigation with scoped completion.
- Updated Intelligent UI reference to the accessible official GPT-6 model guide.
- Expanded [Architecture Overview](architecture/overview.md) to index shared specifications.
- Linked roadmap and the updated architecture from the root README.

### Verified
- [CI run `f7ea930`](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42208829270): 26 passing regression tests, 65 Markdown files, 407 relative links with zero errors, all 56 brand hashes verified; four release conditions remain open.
- Re-read all 27 foundation and Phase 02 documents on `main`; all expected paths resolved. Checked 125 relative Markdown file links against the known document inventory; no missing file targets were found. External links and heading fragments remain outside this check.
