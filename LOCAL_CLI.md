# Local CLI

The local `intel` launcher and the ChatGPT natural-language `/INTEL` convention are **separate**. No command installs a ChatGPT integration or grants external/billable access.

## Start

On Windows, double-click `intel.cmd` for the interactive menu. In any Python 3.12+ terminal run `python intel.py` (interactive) or `python intel.py help`. The Windows launcher forwards arguments to the same Python entrypoint. To expose the name `intel` globally, add your own shell alias or wrapper; no global installation is performed.

```text
intel help
intel version
intel generate prompt --objective "Draft a secure review prompt" --authorize-create
intel config language de
intel config language show
intel config show
intel config validate
intel config export preferences.json
intel config import preferences.json
intel config import preferences.json --apply
intel setup
intel setup --apply
intel providers
intel doctor
intel status
intel test
intel check
intel verify
intel start
```

On non-Windows platforms, replace `intel` with `python intel.py` unless you have installed a shell alias. `intel start` is **Windows-only**, foreground, and invokes the pre-existing PowerShell tunnel launcher. It never starts a tunnel without an explicit command. Stop the tunnel using Ctrl+C in that terminal. The existing `scripts/intel.ps1 -Action ...` actions remain available for tunnel-specific status, doctor, test, Ollama and locating executables.

## CLI behavior

- `generate` delegates to the unchanged `python -m generators` parser, preserving all generator flags, JSON/content output streams, create/external/billable authorization checks, and errors.
- `providers`, `status` and `doctor` are **read-only inspections**. They do not claim that remote services have been contacted or verified.
- `verify` runs the existing local MCP verification script, not a live ChatGPT integration.
- `test` runs the standard-library unittest suite; `check` runs the existing documentation checker and then tests. These may execute repository Python code and are intended for trusted local checkouts.
- `setup` is read-only by default and displays a guided preview; `setup --apply` explicitly initializes the configuration, without changing an already valid file. `dev` remains read-only.
- `config language en|de|show` manages a versioned, allowlisted JSON preference file. The default is English. English and German cover all messages owned by the new CLI, including built-in help, menus, prompts, diagnostics and errors. Legacy generator/PowerShell output stays English to preserve established contracts. Missing keys fall back to English.
- Built-in inspection commands accept `--json`, `--quiet`, `--verbose`, `--no-color` and `--non-interactive` before the subcommand. `--json` is not an alternative to generator-specific `--format json`.
- The terminal UI uses `intel_console.py`, with Unicode-safe cropping, terminal-width-aware rows, status markers and ANSI feature detection (including Windows VT enablement and fallback). Arrow/Enter navigation is available on compatible interactive ANSI terminals, with a numbered plain-text alternative. The interactive prompt/concept/document flow requires explicit confirmation of local CREATE permission. ANSI colors activate only on supported interactive terminals; `NO_COLOR` and non-TTY output are plain text. Inspection JSON is emitted alone on stdout.
- Exit codes: 0 success; 2 usage/authorization/generator error; 3 missing prerequisite or config write failure; subprocess commands preserve the underlying exit code.

## Extending

Commands are registered in the `COMMANDS` mapping and dispatched from `intel.py`. Add a small handler and offline tests; do not add a command that cannot actually function. Generators remain in `generators/` and retain the existing validation and authorization contracts. Provider implementations remain in the provider router; do not add one to CLI inspection as an execution side effect. Add translation keys to both catalogs in `intel_locales.py`; missing keys fall back to English. Add diagnostics to `inspect()` without initiating services or mistaking local configuration for verified connectivity.

## Boundaries and migration

Legacy `python -m generators ...` continues working. `intel.cmd` now forwards into the unified Python shell rather than directly presenting the legacy six-option tunnel menu; the old PowerShell actions remain unchanged and documented. The Python CLI requires Python on PATH. No global `intel` executable is installed and no running-process management is implied. No `stop`, `restart`, `update`, `clean` or `logs` command is advertised without a verified safe implementation.

## Console and localization extension

- All CLI-owned text is keyed in `intel_locales.py`, using matching `en` and `de` catalogs. The catalog regression test guards parity and English fallback. Command syntax, JSON keys, program identifiers, and legacy generator output stay in English.
- `intel_console.py` owns status markers, width handling, ANSI detection, Windows VT fallback, keyboard navigation, and stdout/stderr separation. Avoid raw console formatting in command handlers.
- The interactive menu supports numbers in plain-text terminals and arrows/Enter on capable ANSI terminals. Esc/Q exits. The renderer does not download packages or contact providers.
- `--json` is limited to inspection commands, so it cannot corrupt generator output. Use generator `--format json` for artifact serialization.

## Safe configuration and setup (Phase 03)

See [Local Configuration and Setup](architecture/local-configuration.md) for the schema, source precedence, migration, import/export guarantees and recovery guidance. `intel --language de config show` temporarily selects German; `INTEL_LANGUAGE` overrides persisted preferences but not the explicit CLI flag. Configuration accepts only `schema_version` and `language` - no credentials. `config import PATH` previews a validated import; add `--apply` to authorize the write. `config export PATH` creates a new sanitized file, never overwrites. `setup` previews; `setup --apply` performs idempotent initialization. The existing local generator and MCP permission models are unchanged.

## Lifecycle management (Phase 04)

The original `intel start` still invokes the legacy Windows PowerShell tunnel **in the foreground**; stop it with Ctrl+C. Managed mode is **opt-in**:

```text
intel start --managed
intel status
intel stop
intel restart
```

Managed mode currently supports **Windows tunnels only**. Set `CONTROL_PLANE_API_KEY` explicitly in the invoking terminal, provide an existing `%APPDATA%\\tunnel-client\\chatgpt-intelligence.yaml`, and make `tunnel-client.exe` available on PATH or via `INTEL_TUNNEL_CLIENT`. For other profiles use `INTEL_TUNNEL_PROFILE`. No key file is automatically read and no remote service is invoked without the explicit start/restart command.

A private runtime record stores a 256-bit random control nonce, supervisor PID and loopback-only control port in the user config directory. This is **runtime state**, never configuration export. `status` authenticates the supervisor over loopback, rather than interpreting a PID or port as proof of ownership. `stop` and `restart` refuse an unverified record. They never kill a PID from disk, a foreign listener on 8080, a user-started tunnel or an MCP server. The supervisor only signals its own direct `tunnel-client.exe` child (gracefully first, termination fallback). If the supervisor itself is forcibly killed, child cleanup is not guaranteed; inspect processes before manually repairing stale state.

`python -m generators.mcp_server` remains a stdio server owned by its invoking ChatGPT/MCP host. There is no detached MCP service or automatic restart; generator calls are independent. `intel stop` affects only the CLI-managed tunnel. The local status command does not claim ChatGPT connectivity, profile identity or tunnel readiness merely from port occupancy. An existing runtime record with failed authentication blocks new managed startup and requires manual inspection; it is never silently overwritten or used as a PID-kill target.

## Passive capability and provider registry (Phase 05)

```text
intel generators
intel providers
intel capabilities
intel --json capabilities
intel --json generators
intel --json providers
```

`generators.capabilities` defines the 10 **implemented CLI entrypoints** and static output/provider interfaces; it is distinct from the 16-entry planned `/INTEL` concept registry. The generator CLI imports `GENERATOR_NAMES` to prevent drift, but dispatch and input/format validation stay in their existing runtimes. A catalog entry means **implemented**, not that the generator was executed or a model/provider is reachable.

Provider discovery delegates to existing `ProviderRouter.detect()`, making **no network or file-system probes**, model calls or credential reads. It identifies configured/authorized/verified states without claiming that a configured adapter is reachable. The standalone CLI has no injected ChatGPT host or optional provider credentials, so optional integrations remain **not configured** in discovery. User-facing discovery grants no permissions; `Authorization.require` and generator/host boundaries remain authoritative. The default `template` remains deterministic and offline. `ollama-local` still needs CREATE + EXTERNAL, and `openai-api` needs CREATE + EXTERNAL + BILLABLE. No provider is automatically selected as fallback and no pricing/network operations are triggered by these commands.

Machine-readable output keeps English keys and stable schema identifiers regardless of UI language; use `intel --json capabilities` for the full report. Existing `python -m generators` and MCP invocations retain their arguments and permission checks.

## Developer Automation Toolkit (Phase 06)

The CLI reuses existing scripts without adding parallel implementations. The original unprofiled `intel doctor`, `intel check` and `intel verify` behavior remains compatible. Structured profiles:

```text
intel doctor full
intel --json doctor full
intel check docs
intel check tests
intel check safety
intel --json check all
intel verify mcp --authorize-local-create
intel --json verify release
intel --json dev
intel --json clean
intel --json update
intel --json logs
intel --json logs --file local.log
```

**Boundaries:** `check all` runs the existing Markdown checker followed by unittests. `check safety` reuses the repository's tracked-text credential-signature scan. `verify mcp` runs the existing synthetic stdio verifier **only** after explicit `--authorize-local-create`; it does not connect a ChatGPT client. `verify release` invokes the blocking release gate; existing unmet conditions remain failures. No command bypasses CREATE, EXTERNAL or BILLABLE permissions.

`clean` is strictly a read-only preview; `clean --apply` is **blocked**, not a deletion shortcut. `update` reads **local** Git metadata without fetching the network and always reports `remote_checked: false` and `update_available: null`. It cannot establish the latest upstream commit. `logs` reports the absence of persistent managed logs unless an explicit `--file` is provided. Explicit log reads accept regular non-symlink `.log` or `.txt` files up to 64 KiB, exposing at most the final 100 lines. Credential patterns are redacted **best-effort**, not a guarantee that arbitrary personal data is removed. Never share raw secret-bearing logs.

Profile results have stable English JSON keys: `schema_version`, `command`, `profile`, `status`, `exit_code`, `checks`. Normal status codes are 0 for passed or safe inspection, 1 for a failed check, 2 for invalid usage, and 3 for blocked authorization, environment failures or unsafe operations. Existing unprofiled commands and generators preserve their legacy exit codes. Subprocess stdout/stderr are suppressed for profile runs to avoid accidental credential exposure; inspect underlying tools directly in a trusted environment when detailed failure diagnostics are needed.
