# Rakkase modelleri_indir.ps1. TR: ACE-Step 1.5 model dosyalarini (scripts\modeller.json: revizyona sabit adres, boyut, sha256) indirir ve dogrular.
# EN: downloads and verifies the ACE-Step 1.5 model files listed in scripts\modeller.json (pinned revision, size, sha256).
# Kullanim / usage (PowerShell):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\modelleri_indir.ps1 -Hedef <ACE_KOK>\checkpoints
#   ... -Kuru                 hicbir sey yazmaz, ag kullanmaz: ne indirilecegini ve boyutunu raporlar / dry run: no writes, no network
#   ... -Kaynak <klasor>      var olan checkpoints klasoru: boyutu ve sha256'si tutan dosya KOPYALANIR (indirilmez) / existing folder: matching files are copied
#   ... -Dosya <altdize>      yalniz yolunda bu alt dize gecen dosyalar (ornek: -Dosya vae/config.json) / only files whose path contains this text
# Guvenlik / safety: yalniz modeller.json'daki izinli konaklar (her yonlendirme sicramasinda kontrol), yalniz https, URL'de main yok (revizyon sabit),
#   yol disina cikis yok, sha256 tutmayan dosya yerine KONMAZ (".sha256_uyusmadi" adiyla birakilir, silinmez), .part + Range ile kaldigi yerden surer.
# Durdurma / stop: <kok>\DUR dosyasi -> DURDU (.part korunur).
# Cikis kodlari / exit: 0 tamam, 1 hata (indirme, sha256, tablo), 3 disk yetmiyor, 4 DURDU.
# Kodlar / codes (Hata fonksiyonu 'HATA: [KOD] ...' basar): [RK-E-INDIR] [RK-E-DISK] [RK-W-INDIR-KAYNAK]; harita docs\hata_imzalari.json
# Test (yalniz denetim icin): RK_URL_TABAN doluysa 'https://huggingface.co' on eki bununla degisir ve konagi izinli sayilir (ornek http://127.0.0.1:8099).
param(
    [string]$Hedef = '',
    [string]$Kaynak = '',
    [string]$Dosya = '',
    [switch]$Kuru,
    [switch]$Zorla,
    [double]$MinBosGiB = 1.0
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DurDosya = Join-Path $Root 'DUR'
function Say([string]$m) { Write-Host $m }   # Write-Host: fonksiyon donus degerine karismaz
function Hata([string]$kod, [string]$m) { Write-Host ("HATA: [{0}] {1}" -f $kod, $m) }
function Uyari([string]$kod, [string]$m) { Write-Host ("UYARI: [{0}] {1}" -f $kod, $m) }
function GiB([long]$b) { [Math]::Round($b / 1GB, 2) }

if (-not $Hedef) { Hata 'RK-E-INDIR' 'Hedef klasor verilmedi (-Hedef <ACE_KOK>\checkpoints) / no target folder'; exit 1 }
$tablo = Join-Path $PSScriptRoot 'modeller.json'
try { $kayit = Get-Content -LiteralPath $tablo -Raw -Encoding UTF8 | ConvertFrom-Json } catch { Hata 'RK-E-INDIR' "modeller.json okunamadi ya da bozuk: $($_.Exception.Message)"; exit 1 }
if (-not $kayit.dosyalar -or -not $kayit.revizyon) { Hata 'RK-E-INDIR' 'modeller.json eksik: dosyalar ya da revizyon yok'; exit 1 }
$HedefTam = [IO.Path]::GetFullPath($Hedef)
$izinKonak = @($kayit.izinli_konaklar)
$izinSonEk = @($kayit.izinli_konak_son_ekleri)
$urlTaban = 'https://huggingface.co'   # sha256: her dosya modeller.json'daki $d.sha256 ile dogrulanir (Sha256 $part -ne $d.sha256), tutmazsa yerine konmaz
$testTaban = $env:RK_URL_TABAN
if ($testTaban) { $urlTaban = $testTaban.TrimEnd('/'); $tu = [Uri]$testTaban; $izinKonak += $tu.Host }
function Konak-Izinli([Uri]$u) {
    if ($u.Scheme -ne 'https' -and -not ($testTaban -and $u.Host -eq ([Uri]$testTaban).Host)) { return $false }
    $h = $u.Host.ToLower()
    if ($izinKonak -contains $h) { return $true }
    foreach ($s in $izinSonEk) { if ($h.EndsWith($s)) { return $true } }
    return $false
}
function Yol-Guvenli([string]$rel) {
    if ($rel -match '^[\\/]' -or $rel -match ':' -or [IO.Path]::IsPathRooted($rel)) { return $false }
    foreach ($seg in ($rel -split '[\\/]')) { if ($seg -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or $seg -eq '..' -or $seg -match '[. ]$') { return $false } }
    $tam = [IO.Path]::GetFullPath((Join-Path $HedefTam $rel))
    return $tam.StartsWith($HedefTam.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)
}
function Dur-Kontrol { if (Test-Path -LiteralPath $DurDosya) { Say 'DURDU (DUR dosyasi): .part dosyalari korundu / stopped, .part files kept'; exit 4 } }
function Sha256([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }

# --- 1) Tabloyu dogrula, ne eksik hesapla (yalniz yerel okuma)
$liste = @()
foreach ($d in $kayit.dosyalar) {
    if ($Dosya -and $d.hedef -notlike "*$Dosya*") { continue }
    if (-not (Yol-Guvenli $d.hedef)) { Hata 'RK-E-INDIR' "modeller.json guvensiz yol: $($d.hedef)"; exit 1 }
    if ($d.url -cnotmatch '/resolve/[0-9a-f]{40}/') { Hata 'RK-E-INDIR' "URL revizyona sabit degil (main yasak): $($d.url)"; exit 1 }
    if ($d.sha256 -cnotmatch '^[0-9a-f]{64}$') { Hata 'RK-E-INDIR' "sha256 gecersiz: $($d.hedef)"; exit 1 }
    $liste += $d
}
if ($liste.Count -eq 0) { Hata 'RK-E-INDIR' "eslesen dosya yok (-Dosya '$Dosya')"; exit 1 }
$eksik = @(); $eksikBayt = 0L; $tamam = 0
foreach ($d in $liste) {
    $h = Join-Path $HedefTam $d.hedef
    if ((Test-Path -LiteralPath $h) -and ((Get-Item -LiteralPath $h).Length -eq [long]$d.boyut)) { $tamam++; $eksik += $d; continue }   # sha256 asagida (-Kuru'da hesaplanmaz)
    $eksik += $d
    $part = "$h.part"
    if (Test-Path -LiteralPath $part) { $eksikBayt += [Math]::Max([long]0, [long]$d.boyut - [long](Get-Item -LiteralPath $part).Length) } else { $eksikBayt += [long]$d.boyut }
}
$toplam = ($liste | ForEach-Object { [long]$_.boyut } | Measure-Object -Sum).Sum
Say ("== modelleri_indir: {0} dosya, toplam {1} GiB; hedef {2}" -f $liste.Count, (GiB $toplam), $HedefTam)
Say ("  boyutu tutan (sha256 sonra dogrulanir) {0}; indirilecek ya da kopyalanacak en cok {1} GiB; revizyon {2}" -f $tamam, (GiB $eksikBayt), $kayit.revizyon)
$sur = ''
try { $sur = (Split-Path -Qualifier $HedefTam).TrimEnd(':') } catch { $sur = '' }
$drv = $(if ($sur) { Get-PSDrive -Name $sur -ErrorAction SilentlyContinue } else { $null })
if ($drv) {
    $bosGiB = [Math]::Round($drv.Free / 1GB, 2); Say ("  Disk {0}: bos {1} GiB" -f $sur, $bosGiB)
    if ($eksikBayt -gt 0 -and $bosGiB -lt ((GiB $eksikBayt) + $MinBosGiB)) {
        Hata 'RK-E-DISK' ("model surucusunde bos yer {0} GiB; en az {1} GiB gerekir ({2} GiB model + {3} GiB pay). Yer acin ya da baska surucuye kurun" -f $bosGiB, ((GiB $eksikBayt) + $MinBosGiB), (GiB $eksikBayt), $MinBosGiB); exit 3
    }
}
if ($Kuru) {
    foreach ($d in $eksik) { Say ("  [kuru] {0}  {1} bayt  sha256 {2}..." -f $d.hedef, $d.boyut, $d.sha256.Substring(0, 12)) }
    Say '  KURU: hicbir sey yazilmadi, ag kullanilmadi / dry run: nothing written, no network'
    exit 0
}
# --- 2) Indir / kopyala / dogrula
function Dosya-Indir($d) {
    $h = Join-Path $HedefTam $d.hedef; $part = "$h.part"; $boyut = [long]$d.boyut
    $klasor = Split-Path -Parent $h
    if (-not (Test-Path -LiteralPath $klasor)) { [void](New-Item -ItemType Directory -Path $klasor -Force) }
    if (Test-Path -LiteralPath $h) {
        if ((Get-Item -LiteralPath $h).Length -eq $boyut -and (Sha256 $h) -eq $d.sha256) { Say ("  var, sha256 tutuyor, atlandi: {0}" -f $d.hedef); return $true }
        if (-not $Zorla) { Hata 'RK-E-INDIR' ("var olan dosya beklenenden farkli (boyut ya da sha256): {0}. Tasiyin/silin ve yeniden calistirin, ya da -Zorla (eski dosya .eski olarak saklanir)" -f $h); return $false }
        Move-Item -LiteralPath $h -Destination ("$h.eski") -Force
    }
    # Kaynak klasorden kopya (sha256 tutarsa)
    if ($Kaynak) {
        $k = Join-Path $Kaynak $d.hedef
        if ((Test-Path -LiteralPath $k) -and ((Get-Item -LiteralPath $k).Length -eq $boyut)) {
            Say ("  kaynaktan sha256 bakiliyor: {0}" -f $d.hedef)
            if ((Sha256 $k) -eq $d.sha256) { Copy-Item -LiteralPath $k -Destination $part -Force; Dur-Kontrol; if ((Sha256 $part) -eq $d.sha256) { Move-Item -LiteralPath $part -Destination $h -Force; Say ("  kopyalandi: {0}" -f $d.hedef); return $true } }
            Uyari 'RK-W-INDIR-KAYNAK' ("kaynaktaki dosya sha256 tutmadi, indirilecek: {0}" -f $d.hedef)
        }
    }
    $url = $d.url
    if ($testTaban) { $url = $url -replace '^https://huggingface\.co', $urlTaban }   # sha256: adres degisse de icerik $d.sha256 ile dogrulanir (hash 64 hane, Sha256 $part)
    for ($deneme = 1; $deneme -le 2; $deneme++) {
        $offset = 0L; if (Test-Path -LiteralPath $part) { $offset = (Get-Item -LiteralPath $part).Length }
        if ($offset -gt $boyut) { Move-Item -LiteralPath $part -Destination ("$part.fazla") -Force; $offset = 0L }
        if ($offset -eq $boyut) { break }
        $cur = [Uri]$url; $yanit = $null
        for ($hop = 0; $hop -le 5; $hop++) {
            if (-not (Konak-Izinli $cur)) { Hata 'RK-E-INDIR' ("izinli olmayan adres/yonlendirme reddedildi: {0}" -f $cur.Host); return $false }
            $rq = [Net.HttpWebRequest]::Create($cur); $rq.AllowAutoRedirect = $false; $rq.UserAgent = 'rakkase-kur'; $rq.Timeout = 60000; $rq.ReadWriteTimeout = 60000
            if ($offset -gt 0) { $rq.AddRange([long]$offset) }
            try { $yanit = [Net.HttpWebResponse]$rq.GetResponse() } catch [Net.WebException] {
                $yanit = [Net.HttpWebResponse]$_.Exception.Response
                if (-not $yanit) { Hata 'RK-E-INDIR' ("ag hatasi: {0} ({1}). Baglantiyi kontrol edin, yeniden calistirin: kaldigi yerden surer" -f $_.Exception.Message, $cur.Host); return $false }
            }
            $kod = [int]$yanit.StatusCode
            if ($kod -in 301, 302, 303, 307, 308) { $loc = $yanit.Headers['Location']; $yanit.Close(); if (-not $loc) { Hata 'RK-E-INDIR' 'yonlendirme adresi yok'; return $false }; $cur = New-Object Uri($cur, $loc); $yanit = $null; continue }
            break
        }
        if (-not $yanit) { Hata 'RK-E-INDIR' 'cok fazla yonlendirme'; return $false }
        $kod = [int]$yanit.StatusCode
        if ($kod -eq 416) { $yanit.Close(); if (Test-Path -LiteralPath $part) { Move-Item -LiteralPath $part -Destination ("$part.416") -Force }; continue }
        if ($kod -ne 200 -and $kod -ne 206) { $yanit.Close(); Hata 'RK-E-INDIR' ("sunucu {0} dondurdu: {1}" -f $kod, $d.hedef); return $false }
        $fazla = $false
        $mod = [IO.FileMode]::Append
        if ($kod -eq 200) { $mod = [IO.FileMode]::Create; $offset = 0L }   # sunucu Range'i yok saydi: bastan
        Say ("  indiriliyor: {0} ({1} GiB){2}" -f $d.hedef, (GiB $boyut), $(if ($offset -gt 0) { " kaldigi yerden: $(GiB $offset) GiB" } else { '' }))
        $akis = $yanit.GetResponseStream(); $fs = New-Object IO.FileStream($part, $mod, [IO.FileAccess]::Write)
        try {
            $tampon = New-Object byte[] (1MB); $yazilan = $offset; $sonYuzde = -1; $sayac = 0
            while (($n = $akis.Read($tampon, 0, $tampon.Length)) -gt 0) {
                if ($yazilan + $n -gt $boyut) {   # sunucu beklenenden cok veri yolluyor: en cok 1 bayt fazlasini yaz, kes (disk dolmasin)
                    $fs.Write($tampon, 0, [int]($boyut - $yazilan + 1)); $yazilan = $boyut + 1; $fazla = $true; break
                }
                $fs.Write($tampon, 0, $n); $yazilan += $n; $sayac++
                if ($sayac % 64 -eq 0) { Dur-Kontrol }
                $y = [int](100 * $yazilan / $boyut)
                if ($boyut -gt 100MB -and $y -ge $sonYuzde + 10) { $sonYuzde = $y - ($y % 10); Say ("    %{0}" -f $sonYuzde) }
            }
        } finally { $fs.Close(); $akis.Close(); $yanit.Close() }
        if ($fazla) {
            $fz = "$part.fazla"; Move-Item -LiteralPath $part -Destination $fz -Force
            Hata 'RK-E-INDIR' ("sunucu beklenenden fazla veri gonderdi (beklenen {0} bayt): {1}. Kesildi, dosya silinmedi: {2}. Silip yeniden calistirin" -f $boyut, $d.hedef, $fz); return $false
        }
        break
    }
    if (-not (Test-Path -LiteralPath $part)) { Hata 'RK-E-INDIR' ("indirme tamamlanamadi: {0}" -f $d.hedef); return $false }
    $son = (Get-Item -LiteralPath $part).Length
    if ($son -ne $boyut) { Hata 'RK-E-INDIR' ("boyut tutmadi ({0} / {1} bayt): {2}. .part korundu; yeniden calistirin: kaldigi yerden surer" -f $son, $boyut, $d.hedef); return $false }
    Dur-Kontrol
    $s = Sha256 $part
    if ($s -ne $d.sha256) {
        $ad = "$h.sha256_uyusmadi"; $i = 1; while (Test-Path -LiteralPath $ad) { $i++; $ad = "$h.sha256_uyusmadi$i" }
        Move-Item -LiteralPath $part -Destination $ad
        Hata 'RK-E-INDIR' ("sha256 tutmadi: {0} (beklenen {1}..., gelen {2}...). Dosya silinmedi: {3}. Silip yeniden calistirin" -f $d.hedef, $d.sha256.Substring(0, 12), $s.Substring(0, 12), $ad); return $false
    }
    Move-Item -LiteralPath $part -Destination $h -Force
    Say ("  tamam, sha256 dogrulandi: {0}" -f $d.hedef)
    return $true
}
$basarisiz = 0
foreach ($d in $liste) {
    Dur-Kontrol
    $ok = $false
    try { $ok = [bool](Dosya-Indir $d | Select-Object -Last 1) } catch { Hata 'RK-E-INDIR' ("{0}: {1}" -f $d.hedef, $_.Exception.Message) }   # sha256: Dosya-Indir her dosyada $d.sha256 hash dogrulamasi yapar
    if (-not $ok) { $basarisiz++; break }
}
if ($basarisiz -gt 0) { exit 1 }
Say ("MODELLER HAZIR ({0} dosya, sha256 dogrulandi) / MODELS READY" -f $liste.Count)
exit 0
