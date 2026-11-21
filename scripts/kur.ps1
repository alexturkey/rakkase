# Rakkase kur.ps1: kontrol0 -> klon -> uv -> model -> ayar -> kontrol -> HAZIR.
# TR: ACE-Step 1.5'i (sabit commit) klonlar, uv ile ortami kurar, modelleri sha256 ile indirir, ayarlar.json'i yazar ve plan denetimiyle kontrol eder.
# EN: clones ACE-Step 1.5 (pinned commit), builds the environment with uv, downloads the models with sha256 checks, writes ayarlar.json, runs a plan check.
# Kullanim / usage (PowerShell, repo klasorunde / in the repo folder):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\kur.ps1
#   ... -Kuru     hicbir sey indirmez/kurmaz/yazmaz, ag kullanmaz: tam on rapor (tum HATA ve UYARI tek listede), sonra cikar / dry run: full pre-report, no writes, no network
#   ... -AceKok <yol>        ACE-Step klasoru (varsayilan: ayarlar.json'daki ace_kok, yoksa <repo>\ace_step) / ACE-Step folder
#   ... -ModelKlasoru <yol>  var olan checkpoints klasoru: sha256'si tutan dosya KOPYALANIR, indirilmez / existing checkpoints: matching files are copied
#   ... -Adim kontrol0,klon,uv,model,ayar,kontrol   (varsayilan hepsi; kontrol0 yazilmazsa yalniz secilen adimin on kosulu bakilir)
#   ... -Zorla  (VRAM/RAM sinirini gecer)    -ModelZorla  (sha256 tutmayan var olan model dosyasini .eski yapip yeniden indirir; disk iki katina cikabilir)
# Her adim tekrar calistirilabilir: var olan dogru dosya/klasor atlanir. Durdurma: <repo>\DUR dosyasi -> DURDU.
# Cikis kodlari / exit: 0 HAZIR (ya da -Kuru raporu tamam), 1 hata, 2 girdi/ayar gerek (git ya da uv yok, ayarlar.json bozuk), 3 donanim/disk yetmiyor, 4 DURDU.
#   Kod -> cikis haritasi: docs\hata_imzalari.json (her kodda "cikis" alani).
# Ortam / env: RK_UV (uv.exe yolu), RK_ACE_KOK, UV_CACHE_DIR, UV_PYTHON_INSTALL_DIR (uv'nin kendi degiskenleri; kur.ps1 global ayar degistirmez).
# Test: -Kuru ile RK_KURU_SAHTE='ram=8;bos_ram=2;disk=10;gpu=yok;vram=3000;git=yok;uv=yok;cc=5.2' sahte olcum verir (yalniz -Kuru).
param(
    [string[]]$Adim = @('kontrol0', 'klon', 'uv', 'model', 'ayar', 'kontrol'),
    [switch]$Kuru,
    [string]$AceKok = '',
    [string]$ModelKlasoru = '',
    [switch]$Zorla,
    [switch]$ModelZorla
)
$ErrorActionPreference = 'Stop'
$Adim = @($Adim | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DurDosya = Join-Path $Root 'DUR'
$AyarYol = Join-Path $Root 'ayarlar.json'
$AceUrl = 'https://github.com/ACE-Step/ACE-Step-1.5'
$AceSha = 'ca1e85fe9430179831e6bc6be790c332190a3866'   # tam commit; KURULUM_DEFTERI 2: kod bu commit'le olculdu
$MinBosGiB = 25      # model ~5,94 GiB + uv ortami ve onbellegi (torch cu128 dahil) + pay [olctum: ana oturum, bos E: 823 -> 800 GB = ~23 GB tuketim, kur.log]
$UyariBosGiB = 28
$uyari = New-Object System.Collections.ArrayList
$hata = New-Object System.Collections.ArrayList
$Sahte = @{}
if ($Kuru -and $env:RK_KURU_SAHTE) { foreach ($kv in ($env:RK_KURU_SAHTE -split ';')) { $pp = $kv -split '=', 2; if ($pp.Count -eq 2) { $Sahte[$pp[0].Trim()] = $pp[1].Trim() } } }
function Say([string]$m) { Write-Host $m }
function Sahte-Al([string]$k, $gercek) { if ($Sahte.ContainsKey($k)) { return $Sahte[$k] } else { return $gercek } }
function Hata-Ekle([string]$m, [bool]$zorlaGecer = $false) { if ($zorlaGecer -and $Zorla) { [void]$uyari.Add("(-Zorla ile gecildi) $m") } else { [void]$hata.Add($m) } }
function Dur-Kontrol { if (Test-Path -LiteralPath $DurDosya) { Say 'DURDU (DUR dosyasi) / stopped'; exit 4 } }
function Cikis-Kodu([string[]]$hatalar) {
    # tek sozlesme: docs\hata_imzalari.json "cikis" alani ile ayni
    $k = 1
    foreach ($h in $hatalar) {
        if ($h -match '^\[RK-E-(OS|GPU|GPU-VRAM|RAM|DISK)\]') { return 3 }
        if ($h -match '^\[RK-E-(GIT|UV|AYAR)\]') { $k = 2 }
    }
    return $k
}
function Yol-Uyar([string]$ad, [string]$yol) {
    $oneri = 'Kisa ASCII bir yol onerilir (ornek <SURUCU>:\rk) / a short ASCII path is recommended.'
    if ($yol -match '\s') { [void]$uyari.Add("[RK-W-YOL-BOSLUK] $ad yolu bosluk iceriyor, bu yolda gercek kosu denenmedi: $yol. $oneri") }
    if ($yol -match '[^\x00-\x7F]') { [void]$uyari.Add("[RK-W-YOL-ASCII] $ad yolu ASCII disi karakter (ornek Turkce harf) iceriyor, bu yolda gercek kosu denenmedi: $yol. $oneri") }
    if ($yol -match 'OneDrive') { [void]$uyari.Add("[RK-W-YOL-ONEDRIVE] $ad yolu OneDrive icinde: senkron dosyalari kilitleyebilir, ~6 GB modeli buluta yukler: $yol. $oneri") }
    if ($yol.Length -gt 80) { [void]$uyari.Add("[RK-W-YOL-UZUN] $ad yolu uzun ($($yol.Length) karakter): Windows 260 karakter siniri payi azalir [tahmin]: $yol. $oneri") }
}
function Komut-Bul([string]$ad) { $c = Get-Command $ad -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { return $c.Source } else { return $null } }
function Uv-Bul {
    if ($env:RK_UV -and (Test-Path -LiteralPath $env:RK_UV)) { return $env:RK_UV }
    $u = Komut-Bul 'uv.exe'; if ($u) { return $u }
    $y = Join-Path $env:USERPROFILE '.local\bin\uv.exe'; if (Test-Path -LiteralPath $y) { return $y }
    return $null
}
function Calistir([string]$exe, [string[]]$argumanlar, [string]$dizin = '') {
    # yerel program: stderr'i hata saymaz (git/uv ilerlemeyi stderr'e yazar); cikis kodunu dondurur
    $eski = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    if ($dizin) { Push-Location -LiteralPath $dizin }
    try { & $exe @argumanlar 2>&1 | ForEach-Object { Write-Host ("    " + $_) }; $kod = $LASTEXITCODE } finally { if ($dizin) { Pop-Location }; $ErrorActionPreference = $eski }
    return $kod
}
function Ayar-Oku {
    if (-not (Test-Path -LiteralPath $AyarYol)) { return $null }
    try { return (Get-Content -LiteralPath $AyarYol -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return 'BOZUK' }
}
# AceKok: -AceKok > RK_ACE_KOK > ayarlar.json ace_kok (var ve klasorse) > <repo>\ace_step
$ayar0 = Ayar-Oku
if (-not $AceKok) { $AceKok = $env:RK_ACE_KOK }
if (-not $AceKok -and $ayar0 -and $ayar0 -ne 'BOZUK' -and $ayar0.ace_kok -and (Test-Path -LiteralPath ([string]$ayar0.ace_kok) -PathType Container)) { $AceKok = [string]$ayar0.ace_kok }
if (-not $AceKok) { $AceKok = Join-Path $Root 'ace_step' }
$AceKok = [IO.Path]::GetFullPath($AceKok)
$Checkpoints = Join-Path $AceKok 'checkpoints'

# ------------------------------------------------------------ kontrol0
function Adim-Kontrol0 {
    Say '== kontrol0: donanim ve ortam (hicbir sey indirilmez / nothing is downloaded)'
    if ($Sahte.Count -gt 0) { Say ("  SAHTE OLCUM (yalniz -Kuru testi, RK_KURU_SAHTE): " + (($Sahte.Keys | Sort-Object | ForEach-Object { "$_=$($Sahte[$_])" }) -join ' ')) }
    $os = [Environment]::OSVersion.Version
    Say ("  Windows {0}.{1} build {2}" -f $os.Major, $os.Minor, $os.Build)
    if ($os.Major -lt 10) { Hata-Ekle '[RK-E-OS] Windows 10 ya da ustu gerekir / Windows 10 or newer required' }
    # GPU
    $smi = Komut-Bul 'nvidia-smi.exe'
    $sg = [string](Sahte-Al 'gpu' ''); if ($sg -eq 'yok') { $smi = $null }
    $sahteVar = ($sg -ne '' -and $sg -ne 'yok')
    if (-not $smi -and -not $sahteVar) { Hata-Ekle '[RK-E-GPU] nvidia-smi yok: NVIDIA surucusu kurulu degil ya da NVIDIA kart yok (Rakkase yalniz NVIDIA CUDA). Surucuyu kurun ya da bu bilgisayarda calismaz / no NVIDIA driver or card' }
    else {
        if ($smi) { $q = (& nvidia-smi.exe --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits 2>$null | Select-Object -First 1) } else { $q = "$sg, 4096, sahte, 6.1" }
        if (-not $q) { Hata-Ekle '[RK-E-GPU] nvidia-smi cikti vermedi' }
        else {
            $f = $q -split ',' | ForEach-Object { $_.Trim() }
            $gpuAd = $(if ($sahteVar) { $sg } else { $f[0] }); $vram = [double]$f[1]; $surucu = $f[2]; $cc = $(if ($f.Count -ge 4) { $f[3] } else { '' })
            $vram = [double](Sahte-Al 'vram' $vram); $cc = [string](Sahte-Al 'cc' $cc)
            Say ("  GPU: {0}, {1:N0} MiB, surucu {2}, compute capability {3}" -f $gpuAd, $vram, $surucu, $cc)
            if ($vram -lt 3800) { Hata-Ekle '[RK-E-GPU-VRAM] en az 4 GB ekran karti bellegi (VRAM) gerekir / at least 4 GB VRAM required' $true }
            $ccV = 0.0
            if ([double]::TryParse(($cc -replace ',', '.'), [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$ccV) -and $ccV -lt 6.1) { Hata-Ekle '[RK-E-GPU-VRAM] compute capability 6.1 (Pascal) ya da ustu gerekir (torch cu128)' $true }
            if ($gpuAd -notmatch '1050 Ti') { [void]$uyari.Add("[RK-W-GPU-DENENMEDI] Dogrulanmis donanim yalniz GTX 1050 Ti 4 GB. $gpuAd denenmedi; devam edebilirsiniz ama sonuc garanti degil / untested GPU") }
        }
    }
    # RAM
    $o2 = Get-CimInstance Win32_OperatingSystem
    $ramGB = [double](Sahte-Al 'ram' ([Math]::Round($o2.TotalVisibleMemorySize / 1MB, 1))); $bosGB = [double](Sahte-Al 'bos_ram' ([Math]::Round($o2.FreePhysicalMemory / 1MB, 1)))
    Say ("  RAM: toplam {0} GB, bos {1} GB" -f $ramGB, $bosGB)
    if ($ramGB -lt 12) { Hata-Ekle '[RK-E-RAM] en az 16 GB RAM onerilir (uretimde ~6,4 GB, kurulumda daha fazla); 12 GB alti desteklenmez' $true }
    elseif ($ramGB -lt 15.5) { [void]$uyari.Add("[RK-W-RAM] RAM $ramGB GB: 16 GB onerilir; uretimden once diger uygulamalari kapatin") }
    # git ve uv
    $git = $(if ($Sahte.ContainsKey('git')) { $null } else { Komut-Bul 'git.exe' })
    if (-not $git) { Hata-Ekle '[RK-E-GIT] git yok: ACE-Step kodunu klonlamak icin gerekir. Kurun: winget install --id Git.Git -e (ya da https://git-scm.com) sonra yeniden calistirin / git is missing' }
    else { Say ("  git: {0}" -f $git) }
    $uv = $(if ($Sahte.ContainsKey('uv')) { $null } else { Uv-Bul })
    if (-not $uv) { Hata-Ekle '[RK-E-UV] uv yok: Python ortamini kurmak icin gerekir. Kurun: winget install --id=astral-sh.uv -e (ya da: python -m pip install uv), sonra yeniden calistirin; ya da uv.exe yolunu RK_UV ortam degiskenine yazin / uv is missing (not installed automatically)' }
    else { Say ("  uv: {0}" -f $uv) }
    if (-not $Sahte.ContainsKey('ffmpeg') -and -not (Komut-Bul 'ffmpeg.exe')) { [void]$uyari.Add('[RK-W-FFMPEG] ffmpeg PATH''te yok: mp3 yapilamaz (wav uretilir, kurulum engellenmez). Kurun: winget install --id Gyan.FFmpeg -e / ffmpeg not found: no mp3') }
    # yol uyarilari
    Yol-Uyar 'Kurulum (repo)' $Root; Yol-Uyar 'ACE-Step' $AceKok
    # ACE-Step klasoru
    $aceVar = (Test-Path -LiteralPath $AceKok -PathType Container) -and (@(Get-ChildItem -LiteralPath $AceKok -Force -ErrorAction SilentlyContinue).Count -gt 0)
    if ($aceVar) {
        if (Test-Path -LiteralPath (Join-Path $AceKok 'pyproject.toml')) {
            Say ("  ACE-Step klasoru var, yeniden kurulmaz: {0}" -f $AceKok)
            if ($git -and (Test-Path -LiteralPath (Join-Path $AceKok '.git'))) {
                $eski = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; $h = (& git.exe -C $AceKok rev-parse HEAD 2>$null | Select-Object -First 1); $ErrorActionPreference = $eski
                if ($h -and $h -ne $AceSha) { [void]$uyari.Add("[RK-W-ACE-SURUM] ACE-Step klasoru farkli commit'te ($($h.Substring(0,7)); olculen $($AceSha.Substring(0,7))): dokunulmaz, ama Rakkase olculen surumle dogrulandi / different ACE-Step commit, left untouched") }
            }
        } else { Hata-Ekle "[RK-E-KLON] $AceKok dolu ama bir ACE-Step klasoru degil (pyproject.toml yok): bos bir klasor ya da -AceKok verin" }
    }
    # Disk
    $kayit = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modeller.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $eksikBayt = 0L
    foreach ($d in $kayit.dosyalar) {
        $h2 = Join-Path $Checkpoints $d.hedef
        if ((Test-Path -LiteralPath $h2) -and ((Get-Item -LiteralPath $h2).Length -eq [long]$d.boyut)) { continue }
        $eksikBayt += [long]$d.boyut
    }
    $venvVar = Test-Path -LiteralPath (Join-Path $AceKok '.venv\Scripts\python.exe')
    $gerek = [Math]::Round($eksikBayt / 1GB, 2) + $(if ($venvVar) { 0 } else { ($MinBosGiB - 6) })
    Say ("  Indirilecek model: {0} GiB; uv ortami {1}" -f [Math]::Round($eksikBayt / 1GB, 2), $(if ($venvVar) { 'var' } else { 'kurulacak' }))
    $sh = ''; try { $sh = (Split-Path -Qualifier ([IO.Path]::GetFullPath($AceKok))).TrimEnd(':') } catch { $sh = '' }
    $drv = $(if ($sh) { Get-PSDrive -Name $sh -ErrorAction SilentlyContinue } else { $null })
    if ($drv) {
        $bosGiB = [double](Sahte-Al 'disk' ([Math]::Round($drv.Free / 1GB, 1)))
        Say ("  Disk {0}: bos {1} GiB (gerekli ~{2} GiB)" -f $sh, $bosGiB, $gerek)
        if ($gerek -gt 0 -and $bosGiB -lt $gerek) { Hata-Ekle ("[RK-E-DISK] {0} surucusunde bos yer {1} GiB; en az {2} GiB gerekir (model + uv ortami). Yer acin ya da -AceKok ile baska surucuyu verin / not enough disk" -f $sh, $bosGiB, $gerek) }
        elseif ($gerek -gt 0 -and $bosGiB -lt $UyariBosGiB) { [void]$uyari.Add(("[RK-W-DISK-PAY] {0} surucusunde bos yer {1} GiB: esik ({2} GiB) gecildi ama pay dar" -f $sh, $bosGiB, $gerek)) }
    }
    $ayarDurum = $(if ($ayar0 -eq 'BOZUK') { 'bozuk' } elseif ($ayar0) { 'var' } else { 'yok' })
    Say ("  ayarlar.json: {0}" -f $ayarDurum)
    if ($ayar0 -eq 'BOZUK') { Hata-Ekle '[RK-E-AYAR] ayarlar.json bozuk (JSON okunamadi): dosyaya dokunulmadi. Duzeltin ya da adini degistirip yeniden calistirin / ayarlar.json is not valid JSON' }
}
function Rapor-Ve-Cik {
    foreach ($u in $uyari) { Say ("UYARI: " + $u) }
    foreach ($h in $hata) { Say ("HATA: " + $h) }
    if ($hata.Count -gt 0) { exit (Cikis-Kodu $hata) }
}
function Adim-Hafif {
    # kontrol0 secilmediyse yalniz secilen adimlarin on kosulu: donanim/disk kapisi 'yalniz ayar yaz' gibi kisa islerde engel olmaz
    if ($Adim -contains 'klon' -and -not (Komut-Bul 'git.exe')) { Hata-Ekle '[RK-E-GIT] git yok: ACE-Step kodunu klonlamak icin gerekir. Kurun: winget install --id Git.Git -e / git is missing' }
    if ($Adim -contains 'uv' -and -not (Uv-Bul)) { Hata-Ekle '[RK-E-UV] uv yok: Python ortamini kurmak icin gerekir. Kurun: winget install --id=astral-sh.uv -e; ya da RK_UV / uv is missing' }
    if ($Adim -contains 'ayar' -and $ayar0 -eq 'BOZUK') { Hata-Ekle '[RK-E-AYAR] ayarlar.json bozuk (JSON okunamadi): dosyaya dokunulmadi. Duzeltin ya da adini degistirip yeniden calistirin / ayarlar.json is not valid JSON' }
}
if ($Adim -contains 'kontrol0') { Adim-Kontrol0 } else { Adim-Hafif }
if ($Adim -contains 'kontrol0' -and $Adim.Count -eq 1) { Rapor-Ve-Cik; Say 'KONTROL0 TAMAM / hardware and environment check passed'; exit 0 }
if ($Kuru) {
    Say '== KURU: asagidakiler yapilirdi (hicbir sey yazilmadi, ag kullanilmadi) / dry run: the following would happen'
    $tmpAyar = Join-Path $Root 'ayarlar.json'
    if ($Adim -contains 'klon') { Say ("  klon : git clone {0} {1}; checkout {2}" -f $AceUrl, $AceKok, $AceSha.Substring(0, 12)) }
    if ($Adim -contains 'uv') { Say ("  uv   : uv python install 3.11; uv sync --frozen (klasor {0})" -f $AceKok) }
    if ($Adim -contains 'model') { Say ("  model: scripts\modelleri_indir.ps1 -Hedef {0} (sha256 dogrulamali, ~6 GiB)" -f $Checkpoints) }
    if ($Adim -contains 'ayar') { Say ("  ayar : {0} yazilir/birlestirilir (ace_kok = {1}, kilit=false)" -f $tmpAyar, $AceKok) }
    if ($Adim -contains 'kontrol') { Say '  kontrol: rakkase.py denetle --plan ornekler\sozsuz_fon_ninni.json' }
    Rapor-Ve-Cik
    Say 'KURU TAMAM: hata yok / dry run OK, no errors'
    exit 0
}
Rapor-Ve-Cik
Dur-Kontrol
$uvExe = Uv-Bul; $gitExe = Komut-Bul 'git.exe'

# ------------------------------------------------------------ klon
if ($Adim -contains 'klon') {
    Say '== klon: ACE-Step 1.5 (sabit commit)'
    if (Test-Path -LiteralPath (Join-Path $AceKok 'pyproject.toml')) { Say '  var, atlandi / exists, skipped' }
    else {
        $kod = Calistir $gitExe @('clone', $AceUrl, $AceKok)
        if ($kod -ne 0) { Say "HATA: [RK-E-KLON] git clone basarisiz (cikis $kod). Baglantiyi ve diski kontrol edin; yarim klasoru silip yeniden calistirin / git clone failed"; exit 1 }
        $kod = Calistir $gitExe @('-C', $AceKok, 'checkout', '--detach', $AceSha)
        $eski = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; $h = (& $gitExe -C $AceKok rev-parse HEAD 2>$null | Select-Object -First 1); $ErrorActionPreference = $eski
        if ($kod -ne 0 -or $h -ne $AceSha) { Say "HATA: [RK-E-KLON] commit dogrulanamadi (beklenen $($AceSha.Substring(0,12)), gelen $h) / commit mismatch"; exit 1 }
        Say ("  tamam: {0} @ {1}" -f $AceKok, $AceSha.Substring(0, 12))
    }
}
Dur-Kontrol
# ------------------------------------------------------------ uv
if ($Adim -contains 'uv') {
    Say '== uv: Python 3.11 ve paketler (indirme buyuk olabilir: torch cu128 dahil; yarim kalirsa yeniden calistirin) / Python and packages'
    if (Test-Path -LiteralPath (Join-Path $AceKok '.venv\Scripts\python.exe')) { Say '  .venv var; uv sync yine de calisir (dogrulama, degisiklik yoksa hizli) / .venv exists, sync re-checks' }
    $kod = Calistir $uvExe @('python', 'install', '3.11') $AceKok
    if ($kod -ne 0) { Say "HATA: [RK-E-SYNC] uv python install basarisiz (cikis $kod)"; exit 1 }
    $sync = @('sync'); if (Test-Path -LiteralPath (Join-Path $AceKok 'uv.lock')) { $sync += '--frozen' } else { [void]$uyari.Add('[RK-W-UVLOCK] uv.lock yok, kilitsiz sync') }
    $kod = Calistir $uvExe $sync $AceKok
    if ($kod -ne 0) { Say "HATA: [RK-E-SYNC] uv sync basarisiz (cikis $kod). Ag ve disk bos yerini kontrol edip yeniden calistirin: kaldigi yerden surer / uv sync failed"; exit 1 }
    if (-not (Test-Path -LiteralPath (Join-Path $AceKok '.venv\Scripts\python.exe'))) { Say 'HATA: [RK-E-SYNC] uv sync bitti ama .venv\Scripts\python.exe yok'; exit 1 }
    Say '  tamam: ortam hazir'
}
Dur-Kontrol
# ------------------------------------------------------------ model
if ($Adim -contains 'model') {
    Say '== model: sha256 dogrulamali indirme (scripts\modelleri_indir.ps1)'
    $argM = @{ Hedef = $Checkpoints }; if ($ModelKlasoru) { $argM['Kaynak'] = $ModelKlasoru }; if ($ModelZorla) { $argM['Zorla'] = $true }
    & (Join-Path $PSScriptRoot 'modelleri_indir.ps1') @argM
    $k = $LASTEXITCODE
    if ($k -ne 0) { exit $(if ($k -eq 3 -or $k -eq 4) { $k } else { 1 }) }
}
Dur-Kontrol
# ------------------------------------------------------------ ayar
if ($Adim -contains 'ayar') {
    Say '== ayar: ayarlar.json'
    $ayar = Ayar-Oku
    if ($ayar -eq 'BOZUK') { Say 'HATA: [RK-E-AYAR] ayarlar.json bozuk: dokunulmadi'; exit 2 }
    $yeni = [ordered]@{}
    if ($ayar) { foreach ($p in $ayar.PSObject.Properties) { $yeni[$p.Name] = $p.Value } }
    $mevcutKok = [string]$yeni['ace_kok']
    $yer = ($mevcutKok -eq '' -or $mevcutKok -like '<*')
    if ($yer) { $yeni['ace_kok'] = $AceKok.Replace('\', '/'); Say ("  ace_kok yazildi: {0}" -f $yeni['ace_kok']) }
    elseif ([IO.Path]::GetFullPath($mevcutKok) -ne $AceKok) { Say ("UYARI: [RK-W-AYAR-FARKLI] ayarlar.json ace_kok = {0}; kurulan = {1}. Dokunulmadi; kullanmak icin ayarlar.json'daki satiri degistirin" -f $mevcutKok, $AceKok) }
    else { Say '  ace_kok zaten dogru' }
    foreach ($kv in @(@('kilit', $false), @('kilit_bekle_sn', 3600), @('on_plan_ses_siniri_sn', 300))) { if (-not $yeni.Contains($kv[0])) { $yeni[$kv[0]] = $kv[1] } }
    if (-not $yeni.Contains('kilit_src')) { $yeni['kilit_src'] = '' }
    $json = ($yeni | ConvertTo-Json -Depth 4)
    try { [void]($json | ConvertFrom-Json) } catch { Say 'HATA: [RK-E-AYAR] uretilen ayar JSON degil'; exit 1 }
    [IO.File]::WriteAllText($AyarYol, $json + "`n", (New-Object Text.UTF8Encoding($false)))
    Say ("  yazildi: {0}" -f $AyarYol)
}
Dur-Kontrol
# ------------------------------------------------------------ kontrol
if ($Adim -contains 'kontrol') {
    Say '== kontrol: plan denetimi (CPU, model yuklemez) / plan check'
    $py = Join-Path $AceKok '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $py)) { Say 'HATA: [RK-E-SYNC] .venv yok: once uv adimi'; exit 1 }
    $kod = Calistir $py @('-X', 'utf8', (Join-Path $Root 'rakkase.py'), 'denetle', '--plan', (Join-Path $Root 'ornekler\sozsuz_fon_ninni.json')) $Root
    if ($kod -ne 0) { Say "HATA: [RK-E-SYNC] plan denetimi basarisiz (cikis $kod): yukaridaki satirlara bakin; kodlar docs\SIK_HATALAR.md"; exit 1 }
    foreach ($u in $uyari) { Say ("UYARI: " + $u) }
    Say 'HAZIR / READY: kurulum tamam, plan denetimi gecti.'
    Say 'Sonraki adim / next: python rakkase.py test  (GPU, ~1 dk, referans karsilastirmasi) ya da uret.cmd (ornek plan, parca uretir).'
}
exit 0
