param([string]$BaseUrl)

# .env-ni oxu
$envMap = @{}
Get-Content .\.env | ForEach-Object {
  $l = $_.Trim()
  if($l -and -not $l.StartsWith("#") -and $l.Contains("=")){
    $k,$v = $l.Split("=",2)
    $envMap[$k.Trim()] = $v.Trim()
  }
}

if(-not $BaseUrl){ $BaseUrl = $envMap["LOCAL_API_BASE_URL"] }
$chatModel = $envMap["LOCAL_CHAT_MODEL_NAME"]
$embModel  = $envMap["LOCAL_EMBEDDING_MODEL_NAME"]

Write-Host ">> Base URL: $BaseUrl"
Write-Host ">> Chat model: $chatModel"
Write-Host ">> Emb model: $embModel"

$H = @{ "Content-Type"="application/json" }

# Chat testi
$B1 = @{ model=$chatModel; messages=@(@{role="user";content="Respond with exactly the word: READY"}) } | ConvertTo-Json -Depth 6
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$r1 = Invoke-RestMethod -Uri "$BaseUrl/chat/completions" -Method Post -Headers $H -Body $B1 -TimeoutSec 60
$sw.Stop()
$chatContent = $r1.choices[0].message.content
$okChat = $false
if($chatContent -match '^\s*READY\s*$'){ $okChat = $true }

if($okChat){
  Write-Host ("Chat: PASS in {0}s -> {1}" -f ([math]::Round($sw.Elapsed.TotalSeconds,2)), $chatContent)
}else{
  Write-Host ("Chat: FAIL in {0}s -> {1}" -f ([math]::Round($sw.Elapsed.TotalSeconds,2)), $chatContent)
}

# Embedding testi
$B2 = @{ model=$embModel; input=@("sanity check") } | ConvertTo-Json -Depth 6
$r2 = Invoke-RestMethod -Uri "$BaseUrl/embeddings" -Method Post -Headers $H -Body $B2 -TimeoutSec 60
$len = ($r2.data[0].embedding | Measure-Object).Count

if($len -eq 768){
  Write-Host "Embeddings: PASS len=$len"
}else{
  Write-Host "Embeddings: FAIL len=$len"
}
