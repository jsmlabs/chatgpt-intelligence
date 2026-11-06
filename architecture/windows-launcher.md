---
title: Windows INTEL launcher
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# Windows launcher

Double-click [intel.cmd](../intel.cmd) from the repository root and choose
Start, Status, Doctor, Test, Ollama, or Locate. From Windows PowerShell 5.1:

```powershell
.\scripts\intel.ps1 -Action Start
.\scripts\intel.ps1 -Action Status
.\scripts\intel.ps1 -Action Doctor
.\scripts\intel.ps1 -Action Test
.\scripts\intel.ps1 -Action Ollama
.\scripts\intel.ps1 -Action Locate
```

**Start** discovers `tunnel-client.exe` on PATH, in versioned Windows
Downloads, or under a desktop tunnel-client folder, validates the existing `chatgpt-intelligence` tunnel profile,
sets the working directory to the repository root, runs `doctor` and starts
the foreground tunnel client. Keep the terminal open, and press **Ctrl+C**
to stop. No background service, scheduled task, or restart policy is created.

**Runtime API key:** The launcher first uses `CONTROL_PLANE_API_KEY` if
already set. Otherwise it reads a single-line restricted runtime secret from
`%USERPROFILE%\\Desktop\\tunnel-client\\key.txt` (or the Windows redirected
Desktop equivalent). If the file is absent, it prompts with masked input.
A malformed or empty existing file **blocks startup** rather than falling back
silently. The secret is never printed or committed, and a temporary
environment variable is removed when the action ends. No key or tunnel ID
is saved in repository files. For a custom executable path, pass `-TunnelClient "C:\path\tunnel-client.exe"`
or set `INTEL_TUNNEL_CLIENT`. Existing session credentials are preserved.
Use a restricted Tunnels Read + Use runtime key, not an admin key.

**Status** checks the health and readiness responses at
`http://127.0.0.1:8080`. This is a listener check, not proof of profile
identity or ChatGPT connectivity. If another tunnel is using port 8080, do
not start a duplicate until you have inspected it.

**Doctor** runs the official tunnel-client profile diagnosis.
**Test** runs the existing local synthetic MCP tool verifier without a model
API or tunnel. **Ollama** lists local models; it is not needed for ChatGPT's
`submit_*` tools. No `EXTERNAL` or `BILLABLE` grant is added.

Prerequisite: the profile and private tunnel have already been configured as
described in [ChatGPT MCP host integration](chatgpt-host-integration.md).
The separate chatgpt-context tunnel is not modified.

## Local key-file protection

A plaintext key file is convenient but can be read by other principals with
filesystem access, malware, and potentially desktop-sync/backup software.
Use a **restricted Tunnels Read + Use key**, never an administrator or model
API key. Do not include `key.txt` in this repository. Limit file permissions
to the Windows user, for example from an elevated/trusted local terminal:

```powershell
$keyFile = Join-Path $env:USERPROFILE 'Desktop\tunnel-client\key.txt'
icacls $keyFile
```

Review the listed ACL before modifying it. Prefer a credential manager or
DPAPI-backed secret for stronger at-rest protection; the requested key-file
mode deliberately uses plaintext. Key rotation still requires updating
the local file. Keep the file to **one line**, containing only the full secret
starting with `sk-`, without quotes or additional labels.
