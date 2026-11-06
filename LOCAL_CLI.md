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
- `setup` and `dev` display actionable local instructions only, with no installation, downloads or mutation.
- `config language en|de|show` manages a small JSON preference file. The default is English. German translates the interactive shell and selected status messages. Existing generator and legacy PowerShell messages stay English for compatibility.
- Built-in inspection commands accept `--json`, `--quiet`, `--verbose`, `--no-color` and `--non-interactive` before the subcommand. `--json` is not an alternative to generator-specific `--format json`.
- ANSI colors activate only on supported interactive terminals; `NO_COLOR` and non-TTY output are plain text. Inspection JSON is emitted alone on stdout.
- Exit codes: 0 success; 2 usage/authorization/generator error; 3 missing prerequisite or config write failure; subprocess commands preserve the underlying exit code.

## Extending

Commands are registered in the `COMMANDS` mapping and dispatched from `intel.py`. Add a small handler and offline tests; do not add a command that cannot actually function. Generators remain in `generators/` and retain the existing validation and authorization contracts. Provider implementations remain in the provider router; do not add one to CLI inspection as an execution side effect. Add translation keys to both catalogs in `MESSAGES`; missing keys fall back to English. Add diagnostics to `inspect()` without initiating services or mistaking local configuration for verified connectivity.

## Boundaries and migration

Legacy `python -m generators ...` continues working. `intel.cmd` now forwards into the unified Python shell rather than directly presenting the legacy six-option tunnel menu; the old PowerShell actions remain unchanged and documented. The Python CLI requires Python on PATH. No global `intel` executable is installed and no running-process management is implied. No `stop`, `restart`, `update`, `clean` or `logs` command is advertised without a verified safe implementation.
