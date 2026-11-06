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
