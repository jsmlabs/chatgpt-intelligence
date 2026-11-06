# Changelog

This file records meaningful documentation changes. A proposed design or documentation revision does not imply an implementation or a published software release.

## Unreleased
### Added
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
- Prepared a collision-safe original brand archive layout in `branding/v1.4/`, preserving all 56 original assets and the manifest without replacing independently authored branding guides.
- Recorded binary branding publication and fresh-chat activation as open verification gates, rather than completed integrations.
- Advanced Phase 04 to completed documentation scope; Phase 05 evaluation remains pending.
- Clarified that the repository supports an opt-in ChatGPT usage convention, not an automatically registered slash command or native theme.
- Aligned Phase 03 roadmap status and README navigation with scoped completion.
- Updated Intelligent UI reference to the accessible official GPT-6 model guide.
- Expanded [Architecture Overview](architecture/overview.md) to index shared specifications.
- Linked roadmap and the updated architecture from the root README.

### Verified
- Re-read all 27 foundation and Phase 02 documents on `main`; all expected paths resolved. Checked 125 relative Markdown file links against the known document inventory; no missing file targets were found. External links and heading fragments remain outside this check.
