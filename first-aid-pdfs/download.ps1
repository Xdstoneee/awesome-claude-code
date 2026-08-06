# Download the offline first aid PDF library listed in sources.txt.
# Usage: .\download.ps1 [-OutDir <path>]   (default: .\downloads)
param(
    [string]$OutDir = (Join-Path $PSScriptRoot "downloads")
)

$Sources = Join-Path $PSScriptRoot "sources.txt"
$UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Test-IsPdf([string]$Path) {
    if (-not (Test-Path $Path) -or (Get-Item $Path).Length -eq 0) { return $false }
    $bytes = [System.IO.File]::ReadAllBytes($Path)[0..[Math]::Min(1023, (Get-Item $Path).Length - 1)]
    return ([System.Text.Encoding]::ASCII.GetString($bytes)) -match "%PDF"
}

$ok = 0; $failed = 0; $skipped = 0
$failures = @()

foreach ($line in Get-Content $Sources) {
    $line = $line.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { continue }

    $parts = $line -split "\|"
    $name = $parts[0]
    $urls = $parts[1..($parts.Length - 1)]
    $dest = Join-Path $OutDir $name

    if (Test-IsPdf $dest) {
        Write-Host "SKIP  $name (already downloaded)"
        $skipped++
        continue
    }

    $got = $false
    foreach ($url in $urls) {
        Write-Host "GET   $name"
        Write-Host "      $url"
        try {
            Invoke-WebRequest -Uri $url -OutFile $dest -UserAgent $UA -MaximumRedirection 10 -TimeoutSec 600
            if (Test-IsPdf $dest) { $got = $true; break }
        } catch { }
        Remove-Item -Force -ErrorAction SilentlyContinue $dest
        Write-Host "      ...failed, trying next mirror (if any)"
    }

    if ($got) {
        $size = "{0:N1} MB" -f ((Get-Item $dest).Length / 1MB)
        Write-Host "OK    $name ($size)"
        $ok++
    } else {
        Write-Host "FAIL  $name"
        $failed++
        $failures += $name
    }
}

Write-Host ""
Write-Host "Done: $ok downloaded, $skipped already present, $failed failed."
if ($failed -gt 0) {
    Write-Host "Failed files (try the URLs in sources.txt in a browser):"
    $failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
}
Write-Host "PDFs are in: $OutDir"
