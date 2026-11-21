<!-- One language is enough (English or Turkish); a maintainer adds the other. Tek dil yeter. Draft is fine. Taslak PR olur. -->

## What changes / Ne değişiyor
<!-- 1-3 sentences / 1-3 cümle -->

## Kind / Tür
- [ ] Docs or script / Belge ya da betik
- [ ] Behaviour change / Davranış değişikliği
- [ ] Test report from another machine / Başka makinede test raporu

## Evidence / Kanıt
Label each claim: [measured] [read] [computed] [user-reported] [guess] ([ölçtüm] [okudum] [hesap] [kullanıcı bildirdi] [tahmin]).
<!-- paste the log or numbers, or write "none" / günlük ya da sayıyı yapıştırın, yoksa "yok" -->

## Checks / Kontroller
- [ ] `python -B -I -X utf8 scripts/denetim.py` result / sonuç: <!-- GECTI -->
- [ ] No personal paths, names, e-mails (use the GitHub no-reply address), tokens, model weights or videos / Kişisel yol, ad, e-posta, token, model, video yok
- [ ] No artist names or other people's lyrics in plans / Planlarda sanatçı adı ya da başkasının sözü yok
- [ ] Engine change: `python rakkase.py test` result, or "no GPU, maintainer please run" / Motor değişikliği: `test` sonucu ya da "GPU yok, bakımcı koşsun"
- [ ] Quality settings and the default command line unchanged (turbo 8 steps, int8 decoder only, fp32 compute, LM off) / Kalite ayarları ve varsayılan komut satırı değişmedi
