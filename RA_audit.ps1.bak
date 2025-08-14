param(
  [string]$Root = "."
)

function Get-FileHashSha256($p){ Try { (Get-FileHash -Algorithm SHA256 -Path $p).Hash } Catch { "" } }

function Test-UTF8BOM($path){
  try {
    $fs = [System.IO.File]::OpenRead($path)
    try {
      $buf = New-Object byte[] 3
      $null = $fs.Read($buf,0,3)
      return ($buf[0] -eq 239 -and $buf[1] -eq 187 -and $buf[2] -eq 191)
    } finally { $fs.Dispose() }
  } catch { $false }
}

function Test-Json($path){
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $path
    $null = $raw | ConvertFrom-Json
    return "OK"
  } catch { return "ERROR: $($_.Exception.Message)" }
}

# ---- Secret regex-lər (double-quoted + qaçışlar) ----
$secretPatterns = @(
  "sk-[A-Za-z0-9]{20,}",                              # OpenAI tərzi
  "AKIA[0-9A-Z]{16}",                                 # AWS Access Key
  "-----BEGIN (?:RSA|EC|DSA) PRIVATE KEY-----",
  "(?i)api[_-]?key\s*[:=]\s*[\""'][A-Za-z0-9_\-]{10,}[\""']",
  "(?i)password\s*[:=]\s*[\""'][^\""'\r\n]{6,}[\""']"
) -join '|'

# Skan edərkən istisna ediləcək qovluqlar
$ExcludeDirs = @('\.git\\', '\bnode_modules\\', '\bvenv\\', '\benv\\', 'site-packages\\', 'dist-info\\', '\bbuild\\', '\bdist\\')

# Fayl siyahısı (sonra yol ilə filter)
$all = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
  $full = $_.FullName -replace '/', '\'
  -not ($ExcludeDirs | ForEach-Object { $full -match $_ } | Where-Object { $_ })  # heç birinə uymamalıdır
}

# Qruplar
$byExt = $all | Group-Object Extension | Sort-Object Count -Descending

# Böyük fayllar (≥50MB)
$large = $all | Where-Object { $_.Length -ge 50MB } | Sort-Object Length -Descending

# Konfiq fayllar
$configs = $all | Where-Object {
  $_.Name -match '(^|\.)(env|json|ya?ml|toml|ini)$' -or
  $_.Extension -in '.ps1','.psm1','.py','.js','.ts','.csproj','.sln','.cs','.psd1','.rego' -or
  $_.Name -in 'Dockerfile','docker-compose.yml','docker-compose.yaml','package.json','requirements.txt','pyproject.toml','Pipfile','Pipfile.lock','tsconfig.json'
}

# JSON validasiyası
$jsonFiles   = $all | Where-Object { $_.Extension -eq '.json' -and $_.Name -notmatch 'package-lock.json' }
$jsonResults = foreach($j in $jsonFiles){ [pscustomobject]@{ Path=$j.FullName; Result=(Test-Json $j.FullName) } }

# BOM yoxlaması
$checkBOM = $all | Where-Object { $_.Extension -in '.json','.ps1','.psm1','.py','.yml','.yaml','.txt','.ini','.toml' -or $_.Name -eq '.env' }
$bomResults = foreach($f in $checkBOM){ [pscustomobject]@{ Path=$f.FullName; HasBOM=(Test-UTF8BOM $f.FullName) } }

# Secret scan (yalnız text fayllar)
$textExt   = '.txt','.md','.json','.yaml','.yml','.toml','.ini','.env','.py','.js','.ts','.ps1','.psm1','.cs','.tsx','.jsx'
$textFiles = $all | Where-Object { $_.Extension -in $textExt -or $_.Name -eq '.env' }
$secrets = @()
foreach($t in $textFiles){
  try {
    $content = Get-Content -Raw -Encoding UTF8 $t.FullName
    $m = [regex]::Matches($content,$secretPatterns)
    if($m.Count -gt 0){
      $secrets += [pscustomobject]@{ Path=$t.FullName; Matches=($m.Value | Select-Object -Unique) -join ', ' }
    }
  } catch {}
}

# Endpoint & model axtarışı (double-quoted regex)
$endpointHits = @()
$endpointRegex = "(http[s]?://[^\s\""'\)]+(?:11434|openai\.com|api\.openai\.com)[^\s\""'\)]*)"
$modelRegex    = "(llama3(?::latest)?|gpt-oss:20b|mistral:latest|azeri-llama3:latest|command-r:latest|deepseek-coder:33b|nomic-embed-text:latest)"
foreach($t in $textFiles){
  try{
    $content = Get-Content -Raw -Encoding UTF8 $t.FullName
    $e = [regex]::Matches($content,$endpointRegex)
    $m = [regex]::Matches($content,$modelRegex)
    if($e.Count -gt 0 -or $m.Count -gt 0){
      $endpointHits += [pscustomobject]@{
        Path = $t.FullName
        Endpoints = ($e.Value | Select-Object -Unique) -join ', '
        Models    = ($m.Value | Select-Object -Unique) -join ', '
      }
    }
  } catch {}
}

# .env oxunuşu
$envPath = Join-Path $Root ".env"
$envVars = @()
if(Test-Path $envPath){
  $lines = Get-Content -Encoding UTF8 $envPath
  foreach($ln in $lines){
    if($ln -match '^\s*#' -or -not $ln.Trim()){ continue }
    if($ln -match '^\s*([^=]+)\s*=\s*(.*)$'){
      $envVars += [pscustomobject]@{ Key=$matches[1].Trim(); Value=$matches[2].Trim() }
    }
  }
}

# Bölmələr üçün sətirləri əvvəlcədən hazırla (if ifadə daxilində deyil!)
$lines_byExt = if($byExt){ $byExt | ForEach-Object { "{0,5}  {1}" -f $_.Count, $_.Name } } else { @("None") }
$lines_large = if($large){ $large | ForEach-Object { "{0,10}  {1}" -f ("{0:N1} MB" -f ($_.Length/1MB)), $_.FullName } } else { @("None") }
$lines_configs = if($configs){ $configs | Select-Object -ExpandProperty FullName } else { @("None") }
$lines_json = if($jsonResults){ $jsonResults | ForEach-Object { "$($_.Result)`t$($_.Path)" } } else { @("No .json files") }
$lines_bom = if($bomResults){ $bomResults | ForEach-Object { "$($_.HasBOM)`t$($_.Path)" } } else { @("No files checked") }
$lines_secrets = if($secrets){ $secrets | ForEach-Object { "$($_.Path)`t$($_.Matches)" } } else { @("None") }
$lines_hits = if($endpointHits){ $endpointHits | ForEach-Object { "$($_.Path)`n    Endpoints: $($_.Endpoints)`n    Models   : $($_.Models)" } } else { @("None") }
$lines_env = if($envVars){ $envVars | ForEach-Object { "$($_.Key)=$($_.Value)" } } else { @(".env not found or empty") }

# Hesabat
$report = @()
$report += "=== ResonanceAgent AUDIT REPORT ==="
$report += "Root: $(Resolve-Path $Root)"
$report += "Date: $(Get-Date -Format s)"
$report += ""
$report += "== File counts by extension =="
$report += $lines_byExt
$report += ""
$report += "== Large files (>=50MB) =="
$report += $lines_large
$report += ""
$report += "== Config-like files =="
$report += $lines_configs
$report += ""
$report += "== JSON validation =="
$report += $lines_json
$report += ""
$report += "== UTF-8 BOM check (true=has BOM) =="
$report += $lines_bom
$report += ""
$report += "== Secret scan (potential) =="
$report += $lines_secrets
$report += ""
$report += "== Endpoints & Models found =="
$report += $lines_hits
$report += ""
$report += "== .env parsed =="
$report += $lines_env

$report -join "`r`n" | Set-Content -Encoding UTF8 .\RES_REPORT.txt
Write-Host "Audit hazırdır -> RES_REPORT.txt"
