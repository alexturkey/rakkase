# Contributing / Katkı

## English (authoritative)

Thank you for helping. You do not need to be an expert, and many useful changes (documents, example plans, translations, error tables) need **no GPU at all**; only changes to the engine (`motor/`) need an NVIDIA GPU with 4 GB or more.

**What helps most:** tests on other GPUs (card, driver, plan, time, RAM and VRAM peak, result of `python rakkase.py test`), clearer install steps, new measured recipes for `docs/TARIFLER.md`, typo and translation fixes, and measured memory improvements.

### Your first pull request in 5 steps
1. **Fork** the repository (Fork button on GitHub), then clone your fork.
2. **Branch and change one thing**: `git switch -c fix/short-name`.
3. **Run the checks** (a few seconds, needs Python 3): `python -B -I -X utf8 scripts/denetim.py` (it lists findings and exits 1 if there are any; exit 0 means clean. It is a repository hygiene check, not a music test).
4. **Commit and push** to your fork. Use your GitHub no-reply e-mail (see "Your commit e-mail" below).
5. **Open the pull request** and fill in the short template. Not sure it is ready? Open it as a **draft**; we will say what to fix. Our goal is a first reply within 7 days: a goal of a small volunteer project, not a promise.

### What we accept and what we decline
| Accepted | Declined (with a kind reason) |
|---|---|
| A test report from another GPU, with the log | Lowering the fixed quality settings (turbo 8 steps, int8 decoder only, fp32 compute, LM off) to go faster; the plan field `adim` other than 8 is already an ERROR in `rakkase.py denetle`, and a change that touches it is not merged without a measurement |
| Docs, typo and translation fixes | Model weights, videos, large binaries |
| A script fix that shows the problem and the fix | Claims nobody ran ("should work") |
| A change that keeps the default behaviour identical, or is marked experimental and off by default | Personal paths, names, e-mails, tokens |
| A speed or memory saving with a measurement and the same output | Invisible or bidirectional Unicode, obfuscated code, downloads from hosts not listed in `PRIVACY.md`, telemetry |

A decline is about the rule, never about you.

### Evidence labels (use them in the pull request and in docs)
- **[measured]** you ran it and kept the log or numbers.
- **[read]** you read it in a file or document (give the path).
- **[computed]** derived from measured numbers.
- **[user-reported]** someone else reported it; not reproduced.
- **[guess]** not checked.

Do not write "works" about something you did not run. A labelled guess is welcome; an unlabelled one is not.

### No GPU? You can still help
Read the install steps and tell us where you got stuck, fix a sentence in a translation, add a missing "what you see / what to do" row to `docs/SORUN_GIDERME.md`, send an example plan (original lyrics, no artist names), improve an error message, or run `rakkase.py denetle` on your plans (it needs the ACE-Step folder, not the GPU). These are real contributions.

### One language is enough
Write your pull request in English or Turkish (any language is fine if that is what you have; we will cope). You do not have to write both: if your change touches a section, a maintainer writes the other language. For README content changes edit `README.md` (the English source); translations are updated together by the maintainers. For the license and security text, English is authoritative in every language.

### Your commit e-mail
Commits keep their e-mail in history for good. To keep your address private use the GitHub no-reply address: **GitHub > Settings > Emails > "Keep my email addresses private"**, then `git config user.email "<ID>+<username>@users.noreply.github.com"` (the ID is shown on that page). Commits with another address are accepted; our checks only warn.

### Also
- Security problems: do not open a public issue; see `SECURITY.md`.
- Working with an AI coding agent: read `AGENTS.md` (the agent must never lower the quality settings (8 steps, fp32) to make a run faster).
- Contributions are accepted under the repository's license (MIT). ACE-Step 1.5 code and weights (MIT) and Qwen3-Embedding-0.6B (Apache-2.0) are not distributed here; see `NOTICE`.
- Be kind: `CODE_OF_CONDUCT.md`.

## Türkçe

Teşekkürler. Uzman olmanız gerekmez; işe yarayan değişikliklerin çoğu **4 GB ya da üstü NVIDIA ekran kartı (CUDA) ister**.

**En değerli katkı:** başka kartlarda test (kart, sürücü, plan, süre, RAM ve VRAM tepesi, `python rakkase.py test` sonucu), daha net kurulum adımları, `docs/TARIFLER.md` için ölçülmüş yeni tarifler, yazım ve çeviri düzeltmeleri, ölçülmüş bellek iyileştirmeleri.

### İlk PR'ınız 5 adımda
1. Repoyu **fork'layın** (GitHub'da Fork düğmesi), fork'unuzu klonlayın.
2. **Dal açın, tek şeyi değiştirin**: `git switch -c fix/kisa-ad`.
3. **Kontrolleri çalıştırın** (birkaç saniye, Python 3 gerekir): `python -B -I -X utf8 scripts/denetim.py` (bulgu varsa listeler ve 1 ile çıkar, 0 temiz demektir; depo hijyen denetimidir, müzik testi değil).
4. Fork'unuza **commit ve push**. GitHub no-reply e-postanızı kullanın (aşağıda).
5. **PR açın**, kısa şablonu doldurun. Hazır mı emin değilseniz **taslak (draft)** açın; neyi düzelteceğinizi söyleriz. Hedefimiz ilk yanıtı 7 gün içinde vermek: küçük bir gönüllü projenin hedefi, taahhüdü değil.

### Neyi alırız, neyi geri çeviririz
| Alırız | Gerekçesini nazikçe söyleyerek geri çeviririz |
|---|---|
| Başka kartta test raporu (günlükle) | Hız için sabit kalite ayarlarını (turbo 8 adım, int8 yalnız decoder, fp32 hesap, LM kapalı) düşürmek; plan alanı `adim` 8'den farklıysa `rakkase.py denetle` zaten HATA verir, ona dokunan değişiklik ölçümsüz birleşmez |
| Belge, yazım, çeviri düzeltmesi | Model ağırlığı, video, büyük ikili dosya |
| Sorunu ve çözümü gösteren betik düzeltmesi | Kimsenin çalıştırmadığı iddia ("çalışmalı") |
| Varsayılan davranışı değiştirmeyen ya da deneysel ve varsayılan kapalı işaretli değişiklik | Kişisel yol, ad, e-posta, token |
| Ölçümlü, aynı çıktıyı veren hız ya da bellek kazancı | Görünmez/çift yönlü Unicode, gizlenmiş kod, `PRIVACY.md`'de olmayan adresten indirme, telemetri |

Ret kurala dairdir, size değil.

### Kanıt etiketleri (PR'da ve belgelerde kullanın)
**[ölçtüm]** çalıştırdınız, günlük/sayı elinizde; **[okudum]** dosya ya da belgede okudunuz (yolunu yazın); **[hesap]** ölçülen sayılardan türetildi; **[kullanıcı bildirdi]** başkası bildirdi, tekrarlanmadı; **[tahmin]** denenmedi. Çalıştırmadığınız şey için "çalışır" yazmayın; etiketli tahmin makbuldür.

### ekran kartınız yok mu? Yine de yardım edebilirsiniz
Kurulum adımlarını okuyup nerede takıldığınızı söylemek, bir çeviride cümle düzeltmek, `docs/SORUN_GIDERME.md`'ye eksik bir "ne görürsünüz / ne yapılır" satırı eklemek, örnek plan göndermek (özgün söz, sanatçı adı yok), bir hata mesajını netleştirmek ya da planlarınızda `rakkase.py denetle` koşmak (ACE-Step klasörü ister, GPU istemez) gerçek katkıdır.

### Tek dil yeter
PR'ınızı İngilizce ya da Türkçe yazın (elinizdeki dil neyse o da olur). İkisini birden yazmanız gerekmez: değişiklik bir bölüme dokunuyorsa diğer dili bakımcı yazar. README içerik değişikliği için `README.md`'yi (İngilizce kaynak) düzenleyin; çeviriler bakımcılar tarafından birlikte güncellenir. Lisans ve güvenlik metninde her dilde İngilizce esastır.

### Commit e-postanız
Commit'teki e-posta geçmişte kalıcıdır. Gizli kalması için GitHub no-reply adresini kullanın: **GitHub > Settings > Emails > "Keep my email addresses private"**, sonra `git config user.email "<ID>+<kullanici>@users.noreply.github.com"` (ID aynı sayfada yazar). Başka adresli commit de kabul edilir; kontrollerimiz yalnız uyarır.

### Ayrıca
Güvenlik sorunu: herkese açık issue açmayın, `SECURITY.md`. Yapay zeka ajanıyla çalışıyorsanız `AGENTS.md` (ajan hız için kalite ayarlarını (8 adım, fp32) asla düşürmez). Katkılar deponun lisansı (MIT) altında kabul edilir. ACE-Step 1.5 kodu ve ağırlıkları (MIT) ile Qwen3-Embedding-0.6B (Apache-2.0) burada dağıtılmaz; `NOTICE`'a bakın. Nazik olun: `CODE_OF_CONDUCT.md`.
