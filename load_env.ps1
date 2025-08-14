Get-Content .\.env | ForEach-Object {
  $l = $_.Trim()
  if ($l -and -not $l.StartsWith("#") -and $l.Contains("=")) {
    $k,$v = $l.Split("=",2)
    Set-Item -Path ("Env:{0}" -f $k.Trim()) -Value $v.Trim()
  }
}
Write-Host ".env loaded into current PowerShell process."
