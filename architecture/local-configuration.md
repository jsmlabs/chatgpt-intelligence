# Local Configuration and Setup

The local Python CLI is distinct from ChatGPT's natural-language /INTEL convention. Configuration never grants CREATE, EXTERNAL, BILLABLE, or MCP permissions.

## Quick start

Use `intel.cmd` on Windows or `python intel.py` elsewhere. These commands do not contact external services.

```text
intel setup
intel setup --apply
intel config show
intel config validate
intel config language de
intel config language show
intel config export preferences.json
intel config import preferences.json
intel config import preferences.json --apply
intel doctor
```

## Schema and source of truth

Schema version **1** permits only `schema_version` (integer 1) and `language` (`en` or `de`). Older files containing only `language` remain readable; saved files acquire the version. Unknown fields are rejected (including secrets) rather than silently dropped. No API credentials, provider options, or tunnel keys belong in this configuration.

Effective language precedence: **explicit CLI `--language en|de` > `INTEL_LANGUAGE` environment > persisted user configuration > English default**. The global flag is an invocation-only override; `config language de` persists the selection. `config show --json` is not supported as a post-command global flag; use `intel --json config show`.

User configuration location:
- Windows: `%APPDATA%\\ChatGPTIntelligence\\config.json`
- Linux/macOS: `$XDG_CONFIG_HOME/chatgpt-intelligence/config.json`, or `~/.config/chatgpt-intelligence/config.json`
- Explicit test/portable override: `INTEL_CONFIG_HOME/config.json`

`intel config show` displays effective language and source, not secrets. `intel config validate` checks the file, schema and environment override with actionable messages.

## Mutations and safety

`intel setup` without flags is a **read-only guided preview**. `intel setup --apply` explicitly creates preferences when missing. Repeating it without changes performs no write; invalid existing configuration blocks it. For interactive workflows users can inspect the preview first, then apply.

`intel config export PATH` writes an allowlisted preference-only JSON file with exclusive creation: no overwrite, no symlink destination and no silent directory creation. `intel config import PATH` validates and previews the input, but **never applies it without `--apply`**. The apply path shares the same atomic user config writer as language selection. Symbolic-link input or destination paths, non-JSON files, oversized files, duplicated keys, unknown fields and unsupported versions fail closed. Output paths are explicit and relative paths resolve from the current working directory.

The config file is created through a same-directory temporary file followed by atomic replacement; on Unix the temporary file is mode 0600. This is not a multi-process locking protocol. Avoid concurrent writes and ensure the user profile directory has appropriate permissions. There is no network access, installation, deletion or implicit provider activation.

## Troubleshooting

- **INVALID_CONFIG**: run `intel config validate`; inspect the user JSON, remove unsupported keys using a trusted editor, and retry. Never paste secrets into configuration.
- **Invalid language**: use only `en` or `de`; inspect `INTEL_LANGUAGE` and the CLI override.
- **Cannot write**: check the directory permissions, filesystem availability and symbolic links. No automatic overwrite or permission elevation is attempted.
- **Import preview**: use `--apply` only after reviewing the validated configuration.
- **Existing export path**: choose a new path. Exports never replace existing files.
