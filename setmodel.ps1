param([Parameter(Mandatory=$true)][string]$ModelName)

$envPath = ".\.env"
if (-Not (Test-Path $envPath)) { Write-Error ".env not found in $PWD"; exit 1 }

# .env-d? d?yi?
$content = Get-Content $envPath | ForEach-Object {
  if ($_ -match '^LOCAL_CHAT_MODEL_NAME=') { "LOCAL_CHAT_MODEL_NAME=$ModelName" } else { $_ }
}
Set-Content -Path $envPath -Value $content -Encoding ASCII

# Cari PS sessiyas?nda da d?yi?
$env:LOCAL_CHAT_MODEL_NAME = $ModelName

Write-Host "Model changed to: $ModelName"
