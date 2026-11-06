# Local Runtime Architecture

**Scope:** Implemented local CLI and runtime; not ChatGPT internal architecture. The conversational /INTEL convention in [Command Reference](../COMMANDS.md) is separate from the executable local interface.

## Components and ownership

| Component | Source of truth | Boundary |
| --- | --- | --- |
| Windows launcher | intel.cmd | Forwards into Python CLI |
| Local CLI commands | intel.py | Parser, dispatch, existing generator delegation |
| Console | intel_console.py | ANSI fallback, accessible tables, JSON output |
| Language catalog | intel_locales.py | Complete en/de shell messages; English commands and JSON fields |
| Preferences | intel_config.py | Strict versioned schema, precedence and atomic writes |
| Owned tunnel | intel_lifecycle.py | Windows-only supervisor; never signal an arbitrary PID from disk |
| Developer profiles | intel_devtools.py | Bounded delegation to existing scripts, no duplicate checkers |
| Implemented generators | generators/capabilities.py | Ten CLI types, not a live-provider attestation |
| Reference capabilities | generators/foundation.py | Separate sixteen-entry conceptual /INTEL registry |
| Provider selection | generators/provider_router.py | Deterministic permissions and trusted selection |
| Generator dispatch | generators/__main__.py | Existing formats, validation and grants |
| MCP stdio | generators/mcp_server.py | Host-owned lifecycle; not controlled by intel stop |
| Checks | scripts/check_docs.py, scripts/check_release.py, scripts/check_publication_safety.py | Existing canonical test scripts |

## Execution model

The entrypoint intel.cmd forwards to intel.py. Read-only inspections and maintenance previews stay in the local CLI. Generate delegates to the generator CLI and its runtime; the default template does not contact providers. EXTERNAL and BILLABLE require distinct authorization. Stdio MCP is owned by its invoking host, whereas an explicitly managed Windows tunnel uses a private authenticated supervisor. They are **not** interchangeable lifecycle targets.

Local language precedence: explicit CLI --language > INTEL_LANGUAGE > user config > English. The stored preferences do not contain credentials.

The development toolkit reuses existing Python tests, documentation and publication safety scans, MCP verifier, and release gate. Its update command **does not fetch** and cannot tell whether a remote commit is newer. Clean remains preview-only. Log redaction is best-effort.

## Compatibility and verification

Keep legacy Python generator imports and PowerShell actions intact. Do not consolidate two different registries or rewrite host-owned MCP lifecycle to match Windows tunnel lifecycle. CI checks the local implementation; live provider connectivity, end-user installation, review and publication require separate evidence.

See [Extension Guide](../guides/local-cli-extension.md), [Migration Guide](../guides/local-cli-migration.md), and [Troubleshooting](../guides/local-cli-troubleshooting.md).
