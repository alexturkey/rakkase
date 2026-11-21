"""Soz zamani (ACE-Step'in token duzeyi soz_zamani.json) + plan sozleri -> kelime ve satir zamanlari (karaoke, altyazi, klip).

Kullanim:
  kutuphane: kelimeler(soz_zamani_dict, lyrics, bpm, olcu) -> dict
  komut:     python araclar/kelime_zamani.py <ad>.soz_zamani.json <plan.json> [parca_adi] > <ad>.kelimeler.json
Cikti: {"success", "satirlar": [{"bolum", "metin", "t0", "t1", "olcu", "supheli", "kelimeler": [{"k", "t0", "t1"}]}], "not"}
Supheli satir (docs/SINIRLAR.md, OLCUMLER.md "Soz suresi"): ilk ya da son satir; ayni kareye >= 5 token; token basina < 0,15 sn;
satir suresi 0,6-3,5 olcu disinda. Supheli satirin zamani kullanilmadan once kulakla/gozle bakilir.
Uretim arsivi (araclar/recete.py) bunu her sozlu parca icin kendiliginden yazar.
"""
import json
import sys
from collections import Counter

SUPHELI_MIN_OLCU, SUPHELI_MAX_OLCU = 0.6, 3.5
SUPHELI_TOKEN_SN, SUPHELI_AYNI_KARE = 0.15, 5


def _kelimelere(tokenler):
    kel, cur, bitti = [], None, True
    for t in tokenler:
        s = t.get("text", "")
        if bitti or s[:1] in (" ", "\n"):
            if cur and cur["k"].strip():
                kel.append(cur)
            cur = dict(k="", t0=t["start"], t1=t["end"], n=0, kareler=[])
        cur["k"] += s
        cur["t1"] = t["end"]
        cur["n"] += 1
        cur["kareler"].append(round(t["start"], 2))
        bitti = s.endswith("\n") or s.endswith(" ")
    if cur and cur["k"].strip():
        kel.append(cur)
    temiz, etikette = [], False
    for w in kel:
        m = w["k"].strip()
        if m.startswith("["):
            etikette = True
        if not etikette:
            temiz.append(dict(w, k=m))
        if etikette and m.endswith("]"):
            etikette = False
    return temiz


def kelimeler(sz, lyrics, bpm=None, olcu="4"):
    if not sz or not sz.get("success") or not sz.get("token_timestamps"):
        return {"success": False, "not": f"soz zamani yok ya da basarisiz: {(sz or {}).get('error')}"}
    temiz = _kelimelere(sz["token_timestamps"])
    olcu_sn = (60.0 / float(bpm)) * float(olcu or 4) if bpm else None
    satirlar, bolum, i, uyusmaz = [], "", 0, 0
    for satir in (lyrics or "").splitlines():
        satir = satir.strip()
        if not satir:
            continue
        if satir.startswith("["):
            bolum = satir.strip("[]").split(" -")[0].strip()
            continue
        ks = []
        for w in satir.split():
            if i < len(temiz) and temiz[i]["k"] == w:
                ks.append(temiz[i]); i += 1
            else:
                uyusmaz += 1  # tokenlestirme kelimeyi farkli bolduyse zaman bilinmez; satir yine yazilir
        if not ks:
            satirlar.append(dict(bolum=bolum, metin=satir, t0=None, t1=None, olcu=None, supheli=True, kelimeler=[]))
            continue
        t0, t1 = ks[0]["t0"], ks[-1]["t1"]
        tok = sum(k["n"] for k in ks)
        kare = max(Counter(x for k in ks for x in k["kareler"]).values())
        olc = round((t1 - t0) / olcu_sn, 2) if olcu_sn else None
        supheli = (tok and (t1 - t0) / tok < SUPHELI_TOKEN_SN) or kare >= SUPHELI_AYNI_KARE or \
            (olc is not None and not (SUPHELI_MIN_OLCU <= olc <= SUPHELI_MAX_OLCU))
        satirlar.append(dict(bolum=bolum, metin=satir, t0=round(t0, 2), t1=round(t1, 2), olcu=olc, supheli=bool(supheli),
                             kelimeler=[dict(k=k["k"], t0=round(k["t0"], 2), t1=round(k["t1"], 2)) for k in ks]))
    zamanli = [s for s in satirlar if s["t0"] is not None]
    if zamanli:
        zamanli[0]["supheli"] = zamanli[-1]["supheli"] = True
    return {"success": True, "kaynak": "ACE-Step soz zamani (DiT cross-attention), araclar/kelime_zamani.py",
            "uyusmayan_kelime": uyusmaz, "satirlar": satirlar,
            "not": "supheli=true satirin zamani kulakla/gozle dogrulanmadan kullanilmaz (ilk/son satir hep supheli)"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sz = json.load(open(sys.argv[1], encoding="utf-8"))
    plan = json.load(open(sys.argv[2], encoding="utf-8"))
    parcalar = plan.get("parcalar", [plan])
    p = next((x for x in parcalar if len(sys.argv) < 4 or x.get("ad") == sys.argv[3]), parcalar[0])
    print(json.dumps(kelimeler(sz, p.get("lyrics"), p.get("bpm"), p.get("olcu", "4")), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
