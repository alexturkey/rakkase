# Rakkase tani.ps1 (diagnosis report / teshis raporu)
# EN: Collects a short, privacy-filtered report you can paste into an issue: Windows and PowerShell version, GPU (nvidia-smi),
#     RAM, free disk, the Rakkase version, whether ACE-Step / the Python environment / the model files are where ayarlar.json says (names only, never paths), the dry-run report of kur.ps1 (-Kuru: reads and prints, installs nothing), and
#     optional log files you name with -Log. It then matches the text against docs\hata_imzalari.json (plain sub-strings) and
#     lists the stable error codes (RK-E-...) with the first step. It sends NOTHING: no network, it does not upload or post
#     itself; it only prints (and writes a file if you give -Cikti). Your user name, machine name, home folder, e-mail
#     addresses, tokens, other drive letters and 8.3 short names are replaced with <...> markers before anything is shown.
#     The filter is a rough pattern: READ the report before you paste it; it is not a privacy guarantee.
#       powershell -NoProfile -ExecutionPolicy Bypass -File scripts\tani.ps1                  (text report)
#       ... -File scripts\tani.ps1 -Json                                                       (same as JSON, ASCII)
#       ... -File scripts\tani.ps1 -KartSatiri                                                 (one line for an issue title/card)
#       ... -File scripts\tani.ps1 -Log <SURUCU>:\rk\x.log -Cikti tani_raporu.txt               (add a log, write a file)
#     Options: -KuruAtla (skip the kur.ps1 dry run), -Gizle name1,name2 (extra words to hide), env RK_TANI_GIZLE (same, ';' separated).
# TR: Bir issue'ya yapistirabileceginiz kisa, gizlilik suzgecinden gecmis bir rapor toplar: Windows ve PowerShell surumu, kart
#     (nvidia-smi), RAM, bos disk, Rakkase surumu, kur.ps1 kuru calisma raporu (-Kuru: okur ve yazar, hicbir sey kurmaz) ve
#     -Log ile verdiginiz dosyalar. Sonra metni docs\hata_imzalari.json ile (duz alt dize) eslestirir ve kararli hata kodlarini
#     (RK-E-...) ilk adimla listeler. HICBIR SEY GONDERMEZ: ag yok, kendiliginden yuklemez ve paylasmaz; yalniz ekrana yazar
#     (-Cikti verirseniz dosyaya da yazar). Kullanici adiniz, makine adiniz, ev klasoruz, e-posta, anahtar, diger surucu harfleri ve
#     8.3 kisa adlar gosterilmeden once <...> isaretiyle degistirilir. Suzgec kaba bir desendir: yapistirmadan once raporu OKUYUN;
#     gizlilik garantisi degildir.
# Exit codes / cikis kodlari: 0 report made / rapor uretildi (even if errors were found / hata bulunsa da), 6 could not run / calismadi.
# Safe: it only reads files and runs read-only commands (nvidia-smi, scripts\kur.ps1 -Kuru). No windows, no git, no changes.
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$KartSatiri,
    [switch]$KuruAtla,
    [string[]]$Log = @(),
    [string]$Cikti = '',
    [string[]]$Gizle = @()
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
$kok = Split-Path -Parent $PSScriptRoot

# ------------------------------------------------------------------ gizlilik suzgeci / privacy filter
$adlar = New-Object System.Collections.ArrayList     # @(@{Metin=...; Isaret=...})
function AdEkle([string]$metin, [string]$isaret) {
    if ($metin -and $metin.Trim().Length -ge 3) {
        [void]$adlar.Add(@{ Metin = $metin.Trim(); Isaret = $isaret })
        # JSON \uXXXX escaped form (a non-ASCII name shows up like this in JSON logs): lower and upper hex
        if ($metin -match '[^\x00-\x7F]') {
            foreach ($bicim in @('\u{0:x4}', '\u{0:X4}')) {
                $kc = New-Object System.Text.StringBuilder
                foreach ($ch in $metin.Trim().ToCharArray()) { if ([int]$ch -gt 126) { [void]$kc.AppendFormat($bicim, [int]$ch) } else { [void]$kc.Append($ch) } }
                [void]$adlar.Add(@{ Metin = $kc.ToString(); Isaret = $isaret })
            }
        }
        # a name with spaces also shows up in file names as Name_Part, Name-Part, Name.Part or NamePart
        if ($metin.Trim() -match ' ' -and $isaret -notmatch '^<(ROOT|HOME|TEMP)') {
            foreach ($ayrac in @('_', '-', '.', '')) { [void]$adlar.Add(@{ Metin = ($metin.Trim() -replace ' +', $ayrac); Isaret = $isaret }) }
        }
    }
}
# longest first so that a full path is replaced before the name inside it
AdEkle $kok '<ROOT>'
AdEkle ($kok -replace '\\', '/') '<ROOT>'
AdEkle $env:USERPROFILE '<HOME>'
AdEkle ($env:USERPROFILE -replace '\\', '/') '<HOME>'
AdEkle $env:TEMP '<TEMP>'
AdEkle $env:LOCALAPPDATA '<HOME>\AppData\Local'
AdEkle $env:APPDATA '<HOME>\AppData\Roaming'
AdEkle $env:HOMEPATH '<HOME>'
if ($env:USERPROFILE) { AdEkle (Split-Path -Leaf $env:USERPROFILE) '<USER>' }
AdEkle $env:USERNAME '<USER>'
try { AdEkle ([Environment]::UserName) '<USER>' } catch { }
AdEkle $env:COMPUTERNAME '<MACHINE>'
AdEkle $env:USERDOMAIN '<MACHINE>'
try { AdEkle ([Environment]::MachineName) '<MACHINE>' } catch { }
foreach ($g in $Gizle) { AdEkle $g '<HIDDEN>' }
if ($env:RK_TANI_GIZLE) { foreach ($g in ($env:RK_TANI_GIZLE -split ';')) { AdEkle $g '<HIDDEN>' } }
$adlarSirali = @($adlar | Sort-Object { $_.Metin.Length } -Descending)

$ro = [System.Text.RegularExpressions.RegexOptions]
$IC = $ro::IgnoreCase
# secrets (same families as scripts/denetim.py)
$reSir = New-Object System.Text.RegularExpressions.Regex(('\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}' +
    '|\bAIza[0-9A-Za-z_-]{35}\b|\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{22,}\b|\bhf_[A-Za-z0-9]{30,}\b' +
    '|\bBearer\s+[A-Za-z0-9._~+/=-]{20,}' +
    '|\bgsk_[A-Za-z0-9]{40,}\b|\bxox[abprs]-[A-Za-z0-9-]{10,}|\bAKIA[0-9A-Z]{16}\b|\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b' +
    '|-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|discord(?:app)?\.com/api/webhooks/\d+' +
    '|\b(?:api[_-]?key|secret|token|password|passwd)\s*[=:]\s*[''"][A-Za-z0-9_\-./+=]{16,}[''"]'), $IC)
$reHome1 = New-Object System.Text.RegularExpressions.Regex('\b[A-Za-z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\\/"''`<>|*?\r\n]+', $IC)
$reHome2 = New-Object System.Text.RegularExpressions.Regex('(?<![\w.])/(?:c|mnt/c)/Users/[^/"''`<>|*?\r\n]+', $IC)
$reHome3 = New-Object System.Text.RegularExpressions.Regex('(?<![\w.])/(?:home|Users)/[A-Za-z0-9_.-]+(?=/)', $IC)
$reUnc = New-Object System.Text.RegularExpressions.Regex('\\\\[^\s"''`<>|*?]+', $IC)   # whole UNC path (server, share, folders, file)
# other drives: the folder part goes too (a folder name can be private), the file name stays; a folder name may hold up to 4 words
$reSurucu = New-Object System.Text.RegularExpressions.Regex('(?<![\w`])[D-Zd-z]:[\\/]+(?:[^\\/\s"''`<>|*?]+(?: [^\\/\s"''`<>|*?]+){0,3}[\\/]+)*', $IC)
$reKisa = New-Object System.Text.RegularExpressions.Regex('[A-Za-z0-9_]{2,8}~[0-9](?=[\\/\s"'']|$)', $IC)
$reEposta = New-Object System.Text.RegularExpressions.Regex('(?<![A-Za-z0-9])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b', $IC)

function Gizle-Metin([string]$s) {
    if ([string]::IsNullOrEmpty($s)) { return $s }
    foreach ($a in $adlarSirali) {
        $s = [regex]::Replace($s, [regex]::Escape($a.Metin), $a.Isaret.Replace('$', '$$'), $IC)
    }
    $s = $reHome1.Replace($s, '<HOME>')
    $s = $reHome2.Replace($s, '<HOME>')
    $s = $reHome3.Replace($s, '<HOME>')
    $s = $reUnc.Replace($s, '\\<SERVER>\<DIR>')
    $s = $reSurucu.Replace($s, '<DRIVE>:\<DIR>\')
    $s = $reKisa.Replace($s, '<SHORTNAME>')
    $s = $reSir.Replace($s, '<SECRET>')
    $s = $reEposta.Replace($s, '<EMAIL>')
    # last safety net: if a known name is STILL inside, drop the whole line (fail closed)
    $guvenli = New-Object System.Collections.ArrayList
    foreach ($satir in ($s -split "`r?`n")) {
        $kaldi = $false
        foreach ($a in $adlarSirali) { if ($a.Metin.Length -ge 3 -and $satir.IndexOf($a.Metin, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $kaldi = $true; break } }
        if ($kaldi) { [void]$guvenli.Add('<line removed: a private name survived the filter / satir silindi: ozel ad suzgeci gecti>') } else { [void]$guvenli.Add($satir) }
    }
    return ($guvenli -join "`n")
}

# ------------------------------------------------------------------ olcumler / measurements (read only)
function Say-Hata([string]$m) { [Console]::Error.WriteLine($m) }

$sistem = [ordered]@{ windows = ''; powershell = ''; gpu = ''; vram_mb = ''; surucu = ''; cc = ''; ram_gb = ''; bos_disk_gib = ''; surum = '' }
try { $os = Get-CimInstance Win32_OperatingSystem; $sistem.windows = ('{0} (build {1})' -f $os.Caption, $os.BuildNumber) } catch { $sistem.windows = 'unknown' }
$sistem.powershell = $PSVersionTable.PSVersion.ToString()
try { $cs = Get-CimInstance Win32_ComputerSystem; $sistem.ram_gb = [string][math]::Round($cs.TotalPhysicalMemory / 1GB, 1) } catch { $sistem.ram_gb = 'unknown' }
try {
    $ad = (Split-Path -Qualifier $kok)
    if ($ad -and $ad.Length -ge 2 -and $ad[1] -eq ':') {
        $d = New-Object System.IO.DriveInfo($ad.Substring(0, 1))
        $sistem.bos_disk_gib = [string][math]::Round($d.AvailableFreeSpace / 1GB, 1)
    } else { $sistem.bos_disk_gib = 'unknown' }
} catch { $sistem.bos_disk_gib = 'unknown' }
$sistem.gpu = 'none (nvidia-smi missing or silent)'
$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($smi) {
    foreach ($alanlar in @('name,memory.total,driver_version,compute_cap', 'name,memory.total,driver_version')) {
        try {
            $c = & $smi.Source "--query-gpu=$alanlar" '--format=csv,noheader,nounits' 2>$null
            if ($LASTEXITCODE -eq 0 -and $c) {
                $p = ("$(@($c)[0])" -split ',') | ForEach-Object { $_.Trim() }
                $sistem.gpu = $p[0]; $sistem.vram_mb = $p[1]; $sistem.surucu = $p[2]
                if ($p.Count -ge 4) { $sistem.cc = $p[3] }
                break
            }
        } catch { }
    }
}
if ($sistem.gpu -like 'none*') {
    # No nvidia-smi: add the display adapter NAME only (helps AMD / non-NVIDIA reports). Name only, no ids.
    try {
        $adlar = @(Get-CimInstance Win32_VideoController | ForEach-Object { "$($_.Name)".Trim() } | Where-Object { $_ })
        if ($adlar.Count -gt 0) { $sistem.gpu = $sistem.gpu + '; display adapter: ' + ($adlar -join ' + ') }
    } catch { }
}

# installation state (yes/no only, never the paths): ayarlar.json, ace_kok folder, python environment, model files
$sistem['kurulum'] = ''
try {
    $ay = Join-Path $kok 'ayarlar.json'
    if (-not (Test-Path -LiteralPath $ay)) { $sistem['kurulum'] = 'ayarlar.json: missing / yok' }
    else {
        $aj = Get-Content -LiteralPath $ay -Raw -Encoding UTF8 | ConvertFrom-Json
        $ak = [string]$aj.ace_kok
        $d1 = $(if ($ak -and (Test-Path -LiteralPath $ak -PathType Container)) { 'yes' } else { 'no' })
        $d2 = $(if ($d1 -eq 'yes' -and (Test-Path -LiteralPath (Join-Path $ak '.venv\Scripts\python.exe'))) { 'yes' } else { 'no' })
        $d3 = $(if ($d1 -eq 'yes' -and (Test-Path -LiteralPath (Join-Path $ak 'checkpoints\acestep-v15-turbo\model.safetensors'))) { 'yes' } else { 'no' })
        $sistem['kurulum'] = "ayarlar.json: ok | ace_kok folder: $d1 | python env: $d2 | turbo model file: $d3 | lock: $($aj.kilit)"
    }
} catch { $sistem['kurulum'] = 'ayarlar.json: unreadable / okunamadi' }
$cl = Join-Path $kok 'CHANGELOG.md'
$sistem.surum = 'unknown'
if (Test-Path -LiteralPath $cl) {
    foreach ($satir in (Get-Content -LiteralPath $cl -Encoding UTF8 -TotalCount 80)) {
        if ($satir -match '^##\s+(v\d[^\s]*)') { $sistem.surum = $Matches[1]; break }
    }
}

# the kur.ps1 dry run (read only; it downloads and writes nothing)
$kuru = [ordered]@{ calisti = $false; hata = 0; uyari = 0; satirlar = @() }
$ham = ''
if (-not $KuruAtla) {
    $kurPs = Join-Path $PSScriptRoot 'kur.ps1'
    if (Test-Path -LiteralPath $kurPs) {
        try {
            $ErrorActionPreference = 'Continue'
            $kc = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $kurPs -Kuru 2>&1 | Out-String
            $ErrorActionPreference = 'Stop'
            $ham += $kc + "`n"
            $kuru.calisti = $true
            $sat = New-Object System.Collections.ArrayList
            foreach ($l in ($kc -split "`r?`n")) {
                if ($l -match '^\s*(HATA:|UYARI:)' -or $l -match 'KURU TAMAM' -or $l -match 'Disk .*bos') { [void]$sat.Add($l.TrimEnd()) }
                if ($l -match '^\s*HATA:') { $kuru.hata++ }
                if ($l -match '^\s*UYARI:') { $kuru.uyari++ }
            }
            $kuru.satirlar = @($sat)
        } catch { $ErrorActionPreference = 'Stop'; Say-Hata "UYARI: kur.ps1 -Kuru could not run / calismadi: $($_.Exception.Message)" }
    }
}

# log files the user named (last 400 lines, at most 2 MB each)
$loglar = @()
foreach ($lf in $Log) {
    try {
        $fi = Get-Item -LiteralPath $lf -ErrorAction Stop
        if ($fi.Length -gt 2MB) { $icerik = (Get-Content -LiteralPath $lf -Encoding UTF8 -Tail 400) } else { $icerik = @(Get-Content -LiteralPath $lf -Encoding UTF8) | Select-Object -Last 400 }
        $metin = ($icerik -join "`n")
        $ham += $metin + "`n"
        $loglar += , @{ ad = (Gizle-Metin $fi.Name); satirlar = @(((Gizle-Metin $metin) -split "`n") | Select-Object -Last 20) }
    } catch { $loglar += , @{ ad = '(unreadable / okunamadi)'; satirlar = @() } }
}

# ------------------------------------------------------------------ hata imzasi eslestirme / signature matching (plain sub-strings)
$maskeli = Gizle-Metin $ham
$bulunan = @()
$imzaYol = Join-Path $kok 'docs\hata_imzalari.json'
$imzaDurum = 'ok'
if (Test-Path -LiteralPath $imzaYol) {
    try {
        $j = Get-Content -LiteralPath $imzaYol -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($k in $j.kodlar) {
            $hit = $false
            foreach ($im in $k.imza) { if ($im -and $maskeli.IndexOf([string]$im, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $hit = $true; break } }
            if ($hit) {
                $bulunan += , ([ordered]@{ kod = $k.kod; tur = $k.tur; baslik_en = $k.baslik_en; baslik_tr = $k.baslik_tr; ilk_adim_en = $k.ilk_adim_en; ilk_adim_tr = $k.ilk_adim_tr; capa = $k.capa })
            }
        }
    } catch { $imzaDurum = 'unreadable' }
} else { $imzaDurum = 'missing' }
# errors before warnings
$bulunan = @($bulunan | Sort-Object { if ($_.tur -eq 'hata') { 0 } else { 1 } }, { $_.kod })

$uyari = 'Nothing was sent anywhere. The filter hides names, paths, e-mails and tokens by pattern; read the report before you paste it, it is not a guarantee. / Hicbir yere gonderilmedi. Suzgec adlari, yollari, e-postalari ve anahtarlari desenle gizler; yapistirmadan once raporu okuyun, garanti degildir.'

$sistemM = [ordered]@{}
foreach ($k in $sistem.Keys) { $sistemM[$k] = Gizle-Metin ([string]$sistem[$k]) }
$kuruM = [ordered]@{ calisti = $kuru.calisti; hata = $kuru.hata; uyari = $kuru.uyari; satirlar = @(@($kuru.satirlar) | ForEach-Object { Gizle-Metin $_ }) }
$kodlar = @($bulunan | ForEach-Object { $_.kod })

# ------------------------------------------------------------------ cikti / output
if ($KartSatiri) {
    $kart = 'RK {0} | {1} | {2} {3} MB cc {4} | RAM {5} GB | disk {6} GiB free | kur -Kuru: {7} | imza: {8}' -f $sistemM.surum, $sistemM.windows, $sistemM.gpu, $sistemM.vram_mb, $sistemM.cc, $sistemM.ram_gb, $sistemM.bos_disk_gib, $(if ($kuruM.calisti) { "$($kuruM.hata) HATA $($kuruM.uyari) UYARI" } else { 'not run' }), $(if ($kodlar.Count) { ($kodlar -join ',') } else { 'none' })
    $son = ((Gizle-Metin $kart) -replace '[\r\n]+', ' ')
} elseif ($Json) {
    $nesne = [ordered]@{
        arac = 'Rakkase tani.ps1'; format = 1
        sistem = $sistemM; kuru = $kuruM
        bulunan_kodlar = @($bulunan); imza_dosyasi = $imzaDurum
        loglar = @($loglar); uyari = $uyari
    }
    $js = $nesne | ConvertTo-Json -Depth 6
    # ASCII only: any non-ASCII char becomes \uXXXX (safe on every console code page)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $js.ToCharArray()) { if ([int]$ch -gt 126 -or ([int]$ch -lt 32 -and $ch -ne "`n" -and $ch -ne "`r" -and $ch -ne "`t")) { [void]$sb.AppendFormat('\u{0:x4}', [int]$ch) } else { [void]$sb.Append($ch) } }
    $son = $sb.ToString()
} else {
    $t = New-Object System.Collections.ArrayList
    [void]$t.Add('== Rakkase tani raporu / diagnosis report (nothing is sent / hicbir sey gonderilmez)')
    [void]$t.Add("version / surum : $($sistemM.surum)")
    [void]$t.Add("Windows         : $($sistemM.windows) | PowerShell $($sistemM.powershell)")
    [void]$t.Add("GPU             : $($sistemM.gpu) | VRAM $($sistemM.vram_mb) MB | driver $($sistemM.surucu) | cc $($sistemM.cc)")
    [void]$t.Add("setup / kurulum  : $($sistemM['kurulum'])")
    [void]$t.Add("RAM / disk      : $($sistemM.ram_gb) GB RAM | $($sistemM.bos_disk_gib) GiB free on the drive of the folder / klasorun surucusunde bos")
    if ($kuruM.calisti) {
        [void]$t.Add("kur.ps1 -Kuru   : $($kuruM.hata) HATA, $($kuruM.uyari) UYARI")
        foreach ($l in $kuruM.satirlar) { [void]$t.Add("  $l") }
    } else { [void]$t.Add('kur.ps1 -Kuru   : not run / calistirilmadi') }
    foreach ($lg in $loglar) {
        [void]$t.Add("log $($lg.ad) (last lines / son satirlar):")
        foreach ($l in $lg.satirlar) { [void]$t.Add("  $l") }
    }
    if ($bulunan.Count) {
        [void]$t.Add('error codes found / bulunan hata kodlari:')
        foreach ($b in $bulunan) {
            [void]$t.Add("  [$($b.kod)] $($b.baslik_en) / $($b.baslik_tr)")
            [void]$t.Add("    EN: $($b.ilk_adim_en)")
            [void]$t.Add("    TR: $($b.ilk_adim_tr)")
            [void]$t.Add("    more / ayrinti: $($b.capa)")
        }
    } else { [void]$t.Add("error codes found / bulunan hata kodlari: none / yok (signature file: $imzaDurum)") }
    # DEVIATIONS / SAPMA (read-only): what differs from the defaults. Environment values are never printed, only names.
    [void]$t.Add('deviations / sapma (read-only / salt okur):')
    try {
        $pc = @(Get-Command python -All -ErrorAction SilentlyContinue | Select-Object -First 3)
        if ($pc.Count -gt 0) {
            if ($pc[0].Source -match 'WindowsApps') { [void]$t.Add('  first python on PATH: Microsoft Store shortcut (not a real Python) / PATHte ilk python: Store kisayolu') }
            else { [void]$t.Add('  first python on PATH: ' + ((& $pc[0].Source --version 2>&1) -join ' ')) }
        } else { [void]$t.Add('  no python on PATH / PATHte python yok') }
    } catch { [void]$t.Add('  python order could not be read / python sirasi okunamadi') }
    try {
        $gitK = Get-Command git -ErrorAction SilentlyContinue
        if ($gitK -and (Test-Path -LiteralPath (Join-Path $kok '.git'))) {
            $gs = @(& $gitK.Source --no-optional-locks -C $kok status --short -uno 2>$null | ForEach-Object { "$_".Trim() } | Where-Object { $_ } | Select-Object -First 40)
            if ($gs.Count -eq 0) { [void]$t.Add('  git: tracked files unchanged / izlenen dosyalar degismemis') }
            else { [void]$t.Add("  git: $($gs.Count) tracked file(s) changed (names only) / izlenen dosya degismis (yalniz adlar):"); foreach ($g in $gs) { [void]$t.Add("    $g") } }
        } else { [void]$t.Add('  git: not a git copy or git missing / kopya degil ya da git yok') }
    } catch { [void]$t.Add('  git status could not be read / git durumu okunamadi') }
    $rkEnv = @(Get-ChildItem Env: | Where-Object { $_.Name -like 'RK_*' } | Sort-Object Name | ForEach-Object { "$($_.Name)" })
    if ($rkEnv.Count) { [void]$t.Add('  RK_* variables set (names only) / RK_* degiskenleri (yalniz adlar): ' + ($rkEnv -join ' ')) } else { [void]$t.Add('  RK_* variables: none / yok') }
    [void]$t.Add('  ayarlar.json: ' + $(if (Test-Path -LiteralPath (Join-Path $kok 'ayarlar.json')) { 'exists (values are not printed) / var (degerler basilmaz)' } else { 'missing: copy ayarlar.ornek.json / yok: ayarlar.ornek.json kopyalanir' }))
    [void]$t.Add($uyari)
    $son = ((Gizle-Metin ($t -join "`n")))
}

if ($Cikti) {
    try { [System.IO.File]::WriteAllText($(if ([System.IO.Path]::IsPathRooted($Cikti)) { $Cikti } else { Join-Path (Get-Location).Path $Cikti }), ($son + "`r`n"), (New-Object System.Text.UTF8Encoding($false))) }
    catch { Say-Hata "HATA: could not write the file / dosya yazilamadi: $($_.Exception.Message)"; exit 6 }
}
Write-Output $son
exit 0
