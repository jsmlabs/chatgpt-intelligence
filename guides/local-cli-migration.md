# Local CLI Migration Guide

The /INTEL natural-language convention is **not** an installed ChatGPT command. This guide changes only local tooling. See [Command Reference](../COMMANDS.md).

## Entrypoints

| Existing interface | Current option | Compatibility |
| --- | --- | --- |
| python -m generators prompt --objective "Draft" --authorize-create | Same command, or python intel.py generate prompt --objective "Draft" --authorize-create | The local CLI delegates to the existing generator parser and permission checks |
| scripts/intel.ps1 -Action Start | Same PowerShell action, or intel.cmd start | Both start foreground Windows tunnel flows; stop in the owning terminal |
| scripts/intel.ps1 -Action Doctor | Same PowerShell action, or intel.cmd doctor | CLI doctor inspects local prerequisites, not identical tunnel-specific evidence |
| scripts/intel.ps1 -Action Test | Same PowerShell action, or intel.cmd verify mcp --authorize-local-create | The profiled synthetic MCP verifier requires explicit local-create authorization |
| Previous intel.cmd legacy menu | intel.cmd interactive Python menu | Legacy scripts/intel.ps1 actions stay available |
| Host-owned MCP stdio | Same host invocation | Not owned by intel stop or restart |
| Language-only config.json | intel.cmd config validate | Legacy language-only config remains readable and is versioned on next write |

For Linux/macOS use python intel.py in place of intel.cmd. The local CLI does not install a global executable.

## Safe procedure

1. Run python intel.py help and python intel.py --json capabilities (read-only).
2. Run python intel.py setup to preview and optionally python intel.py setup --apply to persist defaults.
3. Run python intel.py config validate; preferences accept only schema_version and language, not secrets.
4. Verify deterministic local generation using python -m generators prompt --objective "Migration smoke test" --authorize-create. No file is written unless explicit export options are given.
5. Keep your existing tunnel and MCP invocation unless you opt into a new one. Managed tunnel startup is Windows-only and requires explicitly configured prerequisites.
6. In automation, use python intel.py --json doctor full or python intel.py --json check docs instead of parsing decorated terminal output.

## Behavior differences and rollback

The implemented CLI catalog contains ten types; the conceptual registry contains sixteen planned/reference types. The offline template stays the default. Ollama needs CREATE + EXTERNAL; OpenAI API needs CREATE + EXTERNAL + BILLABLE. A configured provider does not imply verified connectivity.

Configuration precedence is CLI --language, then INTEL_LANGUAGE, then user config, then English. Clean only previews; update examines local Git metadata without fetch; logs requires an explicitly selected local file. Restart/stop never kill foreign tunnel processes.

No source files or module imports are moved by this migration. Keep using previous Python/PowerShell entrypoints if your wrapper needs a staged change. See [Troubleshooting](local-cli-troubleshooting.md) and [Architecture](../architecture/local-runtime.md).
