# ACE-Step surecinin ve sistemin bellegini 5 sn'de bir yazar (calistir.py sureci bitene kadar)
param([string]$Cikti = "bellek.csv")
"saat,surec_mb,surec_tepe_mb,bos_ram_mb,sayfa_dosyasi_mb" | Out-File $Cikti -Encoding utf8
while ($true) {
  # venv baslaticisi (uv trampoline) ve asil cocuk surec ayni komut satirini tasir: en buyuk bellekli olan asil surectir (2026-11-05)
  $p = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'calistir.py' } | Sort-Object WorkingSetSize -Descending | Select-Object -First 1
  if (-not $p) { break }
  $g = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue; if (-not $g) { break }
  $os = Get-CimInstance Win32_OperatingSystem; $pf = (Get-CimInstance Win32_PageFileUsage | Measure-Object CurrentUsage -Sum).Sum
  "{0},{1},{2},{3},{4}" -f (Get-Date -Format HH:mm:ss), [int]($g.WorkingSet64/1MB), [int]($g.PeakWorkingSet64/1MB), [int]($os.FreePhysicalMemory/1KB), $pf | Out-File $Cikti -Append -Encoding utf8
  Start-Sleep 5
}
