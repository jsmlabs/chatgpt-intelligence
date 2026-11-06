# Local CLI Extension Guide

This is the extension path for the implemented local runtime. Consult [Architecture](../architecture/local-runtime.md) first.

## Add a CLI command

1. Register its English identifier in intel.py COMMANDS and dispatch() without adding a second router.
2. Add the identifier and desc.identifier to both EN/DE dictionaries in intel_locales.py. JSON keys and command tokens remain English.
3. Only put read-only commands into INSPECTION; emit JSON through Console.report and error messages on stderr.
4. Add bounded offline regression tests under tests/ and update the existing Windows workflow triggers/tests when relevant.
5. Document syntax in [Local CLI](../LOCAL_CLI.md) and adjust migration examples if existing behavior changes.

## Add a generator

1. Implement in generators/ using existing runtime authorization, format and manifest contracts.
2. Register actually implemented types in generators/capabilities.py. The CLI imports GENERATOR_NAMES from that module.
3. Keep the conceptual sixteen-type foundation registry independent; planned capabilities must not be advertised as live.
4. Test valid requests, invalid formats, missing CREATE grants, outputs, and offline defaults.

## Add a provider

Extend generators/provider_router.py deliberately. Trusted caller selection and Authorization.require remain authoritative. Keep configured, authorized and verified states separate. EXTERNAL is required for external invocations; BILLABLE for paid operations. Passive capability inspection cannot probe, invent host tools, download models, or cause charges. Do not silently fall back to a paid provider.

## Add a developer profile

Reuse existing scripts instead of cloning test/docs/release verifiers. Implement bounded orchestration in intel_devtools.py, maintain structured reports/exit codes, and prohibit surprising network or filesystem changes. Clean is intentionally preview-only. Logs expose at most bounded, best-effort-redacted text.

## Verification

In a trusted checkout, run the existing test suite (python -m unittest discover -s tests -v), documentation checker (python scripts/check_docs.py --root .), publication scan (python scripts/check_publication_safety.py --root .), plus python intel.py --json capabilities and python intel.py --json doctor full. Live-provider and release acceptance are separate.

See [Migration](local-cli-migration.md) and [Troubleshooting](local-cli-troubleshooting.md).
