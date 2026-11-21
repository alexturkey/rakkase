# Privacy / Gizlilik

## English (authoritative)

**Short version: Rakkase has no telemetry and its own code opens no network connection.** The only network use is the install you run by hand (below). Nothing about you, your machine or your data is uploaded.

### What you fetch during install (by hand, not by our scripts)
| Host | What | Which step, when |
|---|---|---|
| `github.com` | ACE-Step-1.5 source (pinned commit) | install, by you (`KURULUM.md`) |
| `huggingface.co` | model weights (`ACE-Step/Ace-Step1.5`) | install, by you; generation runs set `HF_HUB_OFFLINE=1` |

The model fingerprints (sha256) we measured are in `docs/KURULUM_DEFTERI.md` (section 3) so you can verify your download. Like any download, the host sees your IP address and the ordinary request headers. We send nothing else: no account, no usernames, no system information, no usage data.

### What it does not do
No telemetry or analytics, no crash reports, no update check, no accounts or cookies, no network ports opened. No upload of plans, lyrics or music.

### What stays on your computer
`ayarlar.json` (your local paths), and `uretimler/` (generated music and recipe archive) inside the project folder; both are git-ignored. Logs can contain your folder path: remove it before you post a log in an issue.

### Good to know
- The engine loads model code from your local ACE-Step checkpoint folder (`trust_remote_code`): download the model only from the official repository above.

### Outside our scripts
- GitHub processes what you post here (issues, pull requests, stars) under the GitHub Privacy Statement; it is public.
- The model and the music it generates are under the ACE-Step license and model card, not under this policy (`NOTICE`).

### Check it yourself (a few seconds, nothing is downloaded)
Every network call in the code: `Select-String -Path rakkase.py,motor/*.py,araclar/*.py -Pattern 'https?://|curl|Invoke-WebRequest|urllib|socket'`. Expected today [read, 2026-11-21]: only `from_pretrained` calls on local folders and one repository address written into the recipe file (`araclar/recete.py`); no connection is opened. If you find a call that is not listed here, please report it as in `SECURITY.md`. When a release adds a host, this file is updated in the same change.

## Türkçe

**Kısaca: Rakkase'da telemetri yok. Kendi kodumuz hiçbir ağ bağlantısı açmaz.** Ağ yalnız sizin elinizle yaptığınız kurulumda kullanılır (aşağıda). Sizin, makinenizin ya da verinizin hiçbir bilgisi yüklenmez.

### Kurulumda sizin indirdikleriniz (elle, betiklerimiz değil)
| Adres | Ne | Hangi adım, ne zaman |
|---|---|---|
| `github.com` | ACE-Step-1.5 kaynağı (sabit commit) | kurulum, sizin elinizle (`KURULUM.md`) |
| `huggingface.co` | model ağırlıkları (`ACE-Step/Ace-Step1.5`) | kurulum, sizin elinizle; üretim `HF_HUB_OFFLINE=1` ile koşar |

Ölçtüğümüz model parmak izleri (sha256) `docs/KURULUM_DEFTERI.md` bölüm 3'te, indirmenizi doğrulayabilirsiniz. Her indirmede olduğu gibi karşı taraf IP adresinizi ve olağan istek başlıklarını görür. Başka hiçbir şey göndermeyiz: hesap, kullanıcı adı, sistem bilgisi, kullanım verisi yok.

### Yapmadıkları
Telemetri/analitik yok, çökme raporu yok, güncelleme denetimi yok, hesap ya da çerez yok, ağ portu açmaz. Plan, söz ya da müzik yüklemez.

### Bilgisayarınızda kalanlar
Proje klasöründe `ayarlar.json` (yerel yollarınız) ve `uretimler/` (üretilen müzik ve reçete arşivi); ikisi de git dışıdır. Günlüklerde klasör yolunuz olabilir: issue'ya günlük koymadan önce silin.

### Bilmeniz iyi olur
- Motor, model kodunu yerel ACE-Step klasörünüzden yükler (`trust_remote_code`): modeli yalnız yukarıdaki resmî depodan indirin.

### Betiklerimizin dışında
- Burada paylaştığınız (issue, PR, yıldız) GitHub tarafından GitHub Gizlilik Bildirimi'ne göre işlenir ve herkese açıktır.
- Model ve ürettiği müzik ACE-Step lisansı ve model kartındadır, bu metnin kapsamı dışındadır (`NOTICE`).

### Kendiniz denetleyin (birkaç saniye, hiçbir şey indirilmez)
Koddaki bütün ağ çağrıları: `Select-String -Path rakkase.py,motor/*.py,araclar/*.py -Pattern 'https?://|curl|Invoke-WebRequest|urllib|socket'`. Bugün beklenen [okudum, 2026-11-21]: yalnız yerel klasörlerde `from_pretrained` çağrıları ve reçete dosyasına yazılan bir depo adresi (`araclar/recete.py`); bağlantı açılmaz. Listede olmayan bir çağrı bulursanız `SECURITY.md`'deki gibi bildirin. Bir sürüm yeni adres eklerse bu dosya aynı değişiklikte güncellenir.
