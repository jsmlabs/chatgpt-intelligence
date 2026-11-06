# Local CLI Troubleshooting

Never delete user files, terminate foreign processes, or overwrite credentials merely to make a check pass.

| Problem | Diagnosis | Safe remedy |
| --- | --- | --- |
| intel.cmd closes instantly | Use an existing Windows terminal | Run intel.cmd help; check Python on PATH |
| Python import failure | Confirm the repository root | Run python intel.py help from that directory |
| Global --json rejected for generation | JSON discovery and artifact formats differ | Use --json before inspection commands; use generator --format json when supported |
| PERMISSION_DENIED | Check provider and grants | Explicitly authorize CREATE and only necessary EXTERNAL/BILLABLE permissions |
| Provider not verified | intel --json providers is passive | Verify separately using the explicitly authorized provider workflow |
| Config invalid | Run python intel.py config validate | Check INTEL_LANGUAGE and the allowlisted user JSON; never put keys in preferences |
| Setup/import made no changes | Preview is the default | Review results; apply only intentionally |
| Export refuses destination | Exclusive output required | Choose a new filename, not an overwrite |
| Tunnel port busy | Check local listener ownership | Do not kill a PID from a status file |
| Managed runtime unverified | Supervisor ownership handshake failed | Inspect manually; do not force stop or overwrite runtime state |
| Foreground tunnel will not stop with intel stop | Not CLI managed | Use Ctrl+C in the owning terminal |
| MCP verification blocked | Requires synthetic local-create grant | Use verify mcp --authorize-local-create only when intended |
| Check profile fails | Captured details suppressed for privacy | Execute the corresponding existing script directly in a trusted checkout |
| Update freshness unknown | No remote fetch | Use an explicit, standard Git remote workflow separately |
| Clean --apply blocked | Preview-only by design | No automatic deletion supported |
| Logs refused | Only bounded regular .log/.txt allowed | Choose an explicit small local UTF-8 file; redaction remains best-effort |
| Release still blocked | Review evidence conditions | Run python scripts/check_release.py --root .; do not bypass release gates |

The documented CLI is available on Python 3.11+; CI checks Linux on 3.11 and Windows on 3.12. See [Migration](local-cli-migration.md) and [Local CLI](../LOCAL_CLI.md).
