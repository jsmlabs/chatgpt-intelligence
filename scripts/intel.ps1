#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Start','Status','Doctor','Test','Ollama','Locate')][string]$Action='Start',
    [string]$Profile='chatgpt-intelligence',
    [string]$TunnelClient=''
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
function ClientPath {
    $explicitPath = $null
    if (-not [string]::IsNullOrWhiteSpace($TunnelClient)) {
        $explicitPath = $TunnelClient
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:INTEL_TUNNEL_CLIENT)) {
        $explicitPath = $env:INTEL_TUNNEL_CLIENT
    }
    if ($explicitPath) {
        if (-not (Test-Path -LiteralPath $explicitPath -PathType Leaf)) {
            throw "Tunnel executable does not exist at: $explicitPath"
        }
        return (Resolve-Path -LiteralPath $explicitPath).Path
    }

    $command = Get-Command tunnel-client.exe -ErrorAction SilentlyContinue
    if ($command -and (Test-Path -LiteralPath $command.Source -PathType Leaf)) {
        return $command.Source
    }

    $downloads = Join-Path $env:USERPROFILE 'Downloads'
    $specific = Join-Path $downloads 'tunnel-client-v0.0.19-windows-amd64\tunnel-client.exe'
    if (Test-Path -LiteralPath $specific -PathType Leaf) {
        return (Resolve-Path -LiteralPath $specific).Path
    }

    if (Test-Path -LiteralPath $downloads -PathType Container) {
        $versions = @(Get-ChildItem -LiteralPath $downloads -Directory -Filter 'tunnel-client-v*-windows-amd64' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending)
        foreach ($dir in $versions) {
            $candidate = Join-Path $dir.FullName 'tunnel-client.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }
        $nested = @(Get-ChildItem -LiteralPath $downloads -File -Recurse -Filter 'tunnel-client.exe' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending)
        foreach ($file in $nested) {
            if (Test-Path -LiteralPath $file.FullName -PathType Leaf) {
                return $file.FullName
            }
        }
    }

    throw 'tunnel-client.exe not found. Use -Action Locate to diagnose or supply -TunnelClient with the full executable path.'
}
function IsHealthy([string]$endpoint,[string]$expected) {
    try {
        $r=Invoke-WebRequest -Uri ("http://127.0.0.1:8080"+$endpoint) -UseBasicParsing -TimeoutSec 3
        return ($r.StatusCode -eq 200 -and $r.Content.Trim() -eq $expected)
    } catch { return $false }
}
function KeyScope([scriptblock]$work) {
    $existing=-not [string]::IsNullOrWhiteSpace($env:CONTROL_PLANE_API_KEY)
    if (-not $existing) {
        $secure=Read-Host 'Tunnel runtime API key' -AsSecureString
        $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $env:CONTROL_PLANE_API_KEY=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $secure.Dispose() }
        if (-not $env:CONTROL_PLANE_API_KEY) { throw 'Empty runtime key.' }
    }
    try { & $work }
    finally {
        if (-not $existing) { Remove-Item Env:\CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue }
    }
}
function RequireProfile {
    if ($Profile -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid profile name.' }
    $p=Join-Path (Join-Path $env:APPDATA 'tunnel-client') ($Profile+'.yaml')
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing profile '$Profile'. Run tunnel-client init." }
}
$prior=Get-Location
try {
    Set-Location -LiteralPath $root
    switch ($Action) {
        'Locate' {
            $located = ClientPath
            Write-Host "Tunnel client: $located"
            & $located --version
            if ($LASTEXITCODE -ne 0) { throw "Tunnel executable failed with exit code $LASTEXITCODE" }
        }
        'Status' {
            $live=IsHealthy '/healthz' 'live'
            $ready=IsHealthy '/readyz' 'ready'
            Write-Host ("Health: "+$(if($live){'LIVE'}else{'OFFLINE'}))
            Write-Host ("Ready:  "+$(if($ready){'READY'}else{'NOT READY'}))
            if($ready){Write-Host 'Dashboard: http://127.0.0.1:8080/ui'}
            if(-not $ready){exit 1}
        }
        'Test' {
            $python=Get-Command python -ErrorAction SilentlyContinue
            if(-not $python){throw 'Python not on PATH.'}
            & $python.Source -m scripts.verify_host_mcp --authorize-local-create
            if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
        }
        'Ollama' {
            $ollama=Get-Command ollama -ErrorAction SilentlyContinue
            if(-not $ollama){throw 'Ollama not installed (optional for ChatGPT MCP).'}
            & $ollama.Source list
            if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
        }
        'Doctor' {
            RequireProfile
            $client=ClientPath
            KeyScope {
                & $client doctor --profile $Profile --explain
                if($LASTEXITCODE -ne 0){throw "Doctor failed: $LASTEXITCODE"}
            }
        }
        'Start' {
            RequireProfile
            $client=ClientPath
            if(-not (Get-Command python -ErrorAction SilentlyContinue)){throw 'Python not on PATH.'}
            if(IsHealthy '/healthz' 'live'){throw 'Port 8080 is already used by a tunnel health listener; check its profile before starting another.'}
            Write-Host "INTEL: starting '$Profile' from $root"
            Write-Host 'Keep terminal open; Ctrl+C stops the tunnel.'
            KeyScope {
                & $client doctor --profile $Profile
                if($LASTEXITCODE -ne 0){throw "Doctor failed: $LASTEXITCODE"}
                & $client run --profile $Profile
                if($LASTEXITCODE -ne 0){throw "Tunnel exited: $LASTEXITCODE"}
            }
        }
    }
} catch {
    Write-Error $_.Exception.Message
    exit 1
} finally { Set-Location -LiteralPath $prior }
