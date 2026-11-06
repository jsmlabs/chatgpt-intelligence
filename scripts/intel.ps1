#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Start','Status','Doctor','Test','Ollama')][string]$Action='Start',
    [string]$Profile='chatgpt-intelligence',
    [string]$TunnelClient=''
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
function ClientPath {
    if ($TunnelClient) { $path=$TunnelClient }
    elseif ($env:INTEL_TUNNEL_CLIENT) { $path=$env:INTEL_TUNNEL_CLIENT }
    else {
        $found=Get-Command tunnel-client.exe -ErrorAction SilentlyContinue
        if ($found) { return $found.Source }
        $found=Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Downloads') -Filter tunnel-client.exe -Recurse -File -ErrorAction SilentlyContinue |
          Where-Object { $_.FullName -match 'tunnel-client-v[0-9].*-windows-amd64' } |
          Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($found) { return $found.FullName }
        throw 'tunnel-client.exe not found. Download it or set INTEL_TUNNEL_CLIENT.'
    }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Tunnel client executable not found.' }
    return (Resolve-Path -LiteralPath $path).Path
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
