"""Uretim oncesi plan denetimi (CPU, GPU/model yuklemeden; ~3-5 sn tokenizer yuklemesi).
Amac (kullanici 2026-11-05): "bu hatalar olusmadan, biz yazmadan bilebilmeliyiz".

  <ACE venv python> araclar/denetle.py --plan plan.json [--yalniz ad1,ad2] [--json]
  cikis 0 = temiz ya da yalniz UYARI, 2 = HATA (uretim baslamaz; rakkase.py uret --denetimsiz ile atlanir)

Kontroller ve kaynaklari (docs/KULLANIM.md "Plan denetimi"):
  - caption + metas: paketin kendi sablonu (SFT_GEN_PROMPT + DEFAULT_DIT_INSTRUCTION + metas), tokenizer Qwen3-Embedding-0.6B,
    sinir 256 (conditioning_text.py, truncation=True: asan kisim sondan kesilir, once metas ve caption sonu gider)
  - lyrics: "# Languages\n<dil>\n\n# Lyric\n<soz><|endoftext|>", sinir 2048
  - sure sozlere yeter mi: olculmus kaba kural (rap 92 bpm iki kosu; balad 80 + koro 70 bpm; docs/OLCUMLER.md "Soz suresi"), yalniz UYARI
  - alan tipleri, adim=8 (kalite degismezi), vocal_language paketin VALID_LANGUAGES listesinde, shift (0, 5]
Esikler docs/SINIRLAR.md ile ayni olmali; testler/denetle_test.py ikisini karsilastirir.
"""
import argparse
import json
import os
import re
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(KOK, "ayarlar.json"), encoding="utf-8") as _f:
    AYAR = json.load(_f)

CAPTION_SINIR, CAPTION_UYARI = 256, 240
SOZ_SINIR, SOZ_UYARI = 2048, 1800
SURE_UYARI = 300          # ustunde DiT adimi dogrusal buyumuyor (360 sn: 45 sn/adim, VRAM tasmasi; OLCUMLER)
# Soz suresi kurali (olcum 2026-11-05, soz_zamani): sozlu [Intro] ~4 olcu; rap satiri ~1,15 olcu (92 bpm, 30 sn'de nakarat
# sikisti, 40 sn'de sigdi); sarki satiri ~2 olcu (saglam satirlar: balad 80 bpm ort. 1,9, koro 70 bpm ort. 2,0). Iki-uc ornek.
GIRIS_OLCU, RAP_SATIR_OLCU, SARKI_SATIR_OLCU, BITIS_PAYI_OLCU = 4.0, 1.15, 2.0, 1.0
KALITE_ADIM = 8           # turbo modelin kendi degeri; degismez (CLAUDE.md)
SESLI = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")
VOKAL_DESEN = re.compile(r"\b(vocals?|rapper|rap|singer|singing|choir|mc|sung|lyrics)\b")  # kelime siniri: "trap", "therapy" eslesmez
RAP_DESEN = re.compile(r"\brap\b")
ENSTRUMANTAL_DESEN = re.compile(r"\bno vocals\b|\binstrumental (track|piece|music|only|version)\b|^\s*instrumental\b")


def hece(s):
    s = re.sub(r"\(.*?\)", "", s)
    return sum(1 for ch in s if ch in SESLI)


def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(os.path.join(AYAR["ace_kok"], "checkpoints", "Qwen3-Embedding-0.6B"))


def gecerli_diller():
    sys.path.insert(0, AYAR["ace_kok"])
    from acestep.constants import VALID_LANGUAGES
    return set(VALID_LANGUAGES)


def caption_metni(p):
    sys.path.insert(0, AYAR["ace_kok"])
    from acestep.constants import SFT_GEN_PROMPT, DEFAULT_DIT_INSTRUCTION
    metas = (f"- bpm: {p.get('bpm') or 'N/A'}\n- timesignature: {p.get('olcu') or 'N/A'}\n- keyscale: {p.get('ton') or 'N/A'}\n"
             f"- duration: {int(p['sure'])} seconds\n")
    return SFT_GEN_PROMPT.format(DEFAULT_DIT_INSTRUCTION, p["caption"], metas)


def bolumler(soz):
    """[Etiket] -> satirlar. Etiket adi kucuk harf."""
    out, ad = [], None
    for sat in soz.splitlines():
        sat = sat.strip()
        if not sat:
            continue
        if sat.startswith("[") and sat.endswith("]"):
            ad = sat[1:-1].lower(); out.append([ad, []]); continue
        if ad is None:
            ad = ""; out.append([ad, []])
        out[-1][1].append(sat)
    return out


def gereken_sure(p, bol):
    bpm = float(p.get("bpm") or 0)
    if bpm <= 0:
        return None
    olcu = 60.0 / bpm * float(p.get("olcu") or 4)
    toplam = BITIS_PAYI_OLCU
    for ad, satirlar in bol:
        if ad.startswith("intro"):
            toplam += GIRIS_OLCU
            continue
        if ad.startswith("instrumental") or "break" in ad or "solo" in ad or "interlude" in ad:
            toplam += 4.0
            continue
        katsayi = RAP_SATIR_OLCU if (RAP_DESEN.search(ad) or RAP_DESEN.search(p["caption"].lower())) else SARKI_SATIR_OLCU
        toplam += katsayi * len(satirlar)
    return round(toplam * olcu, 1)


def sayi_mi(x, tam=False):
    return not isinstance(x, bool) and (isinstance(x, int) if tam else isinstance(x, (int, float)))


def denetle(p, tok, adlar, diller=None):
    bulgu = []
    H = lambda m: bulgu.append(("HATA", m))
    U = lambda m: bulgu.append(("UYARI", m))
    if not isinstance(p, dict):
        return [("HATA", "parca bir JSON nesnesi degil")], {}
    for alan in ("ad", "caption", "sure", "tohum", "bpm", "ton", "olcu"):
        if alan not in p:
            H(f"zorunlu alan yok: {alan}")
    if any(d == "HATA" for d, _ in bulgu):
        return bulgu, {}
    if not isinstance(p["ad"], str) or not p["ad"] or any(c in p["ad"] for c in '\\/:*?"<>|'):
        H("'ad' bos olmayan, dosya adina uygun bir yazi olmali")
    if not isinstance(p["caption"], str) or not p["caption"].strip():
        H("'caption' bos olmayan bir yazi olmali")
    if not sayi_mi(p["sure"]):
        H("'sure' sayi olmali (saniye)")
    if not sayi_mi(p["tohum"], tam=True):
        H("'tohum' tam sayi olmali")
    if not sayi_mi(p["bpm"]) or not 30 <= p["bpm"] <= 300:
        H("'bpm' 30-300 arasi sayi olmali")
    if not isinstance(p["olcu"], str) or p["olcu"] not in ("2", "3", "4", "6"):
        H("'olcu' yazi olarak \"2\", \"3\", \"4\" ya da \"6\" olmali (paket .strip() cagirir; sayi verilirse yuklemeden sonra coker)")
    if not isinstance(p["ton"], str):
        H("'ton' yazi olmali (ornek \"G Major\"; paket .strip() cagirir)")
    if "vocal_language" in p and not isinstance(p["vocal_language"], str):
        H("'vocal_language' yazi olmali (ornek \"tr\")")
    if p.get("lyrics") is not None and not isinstance(p["lyrics"], str):
        H("'lyrics' yazi olmali")
    if "adim" in p and p["adim"] != KALITE_ADIM:
        H(f"adim {p['adim']}: kalite degismezi {KALITE_ADIM} (turbo modelin kendi degeri); alani sil")
    if p.get("gorev", "text2music") not in ("text2music", "cover"):
        H("'gorev' yalniz \"text2music\" ya da \"cover\" (2026-11-07)")
    elif p.get("gorev") == "cover":
        if not p.get("kaynak_ses") or not os.path.isfile(p["kaynak_ses"]):
            H("cover: 'kaynak_ses' var olan bir ses dosyasi olmali")
        if "cover_gucu" in p and (not sayi_mi(p["cover_gucu"]) or not 0 < p["cover_gucu"] <= 1):
            H("'cover_gucu' (0, 1] arasi sayi olmali (8 adimin ilk int(8*g) adimi kaynakla)")
    if "shift" in p:
        if not sayi_mi(p["shift"]) or not 0 < p["shift"] <= 5:
            H("'shift' (0, 5] arasi sayi olmali (varsayilan 1.0)")
        elif p["shift"] != 1.0 and p.get("soz_zamani", bool((p.get("lyrics") or "").strip()) and (p.get("lyrics") or "").strip().lower() != "[instrumental]"):
            U("shift != 1 iken soz_zamani: paketin hizalamasi son adimi t=1/adim varsayar, zamanlar kayabilir")
    if any(d == "HATA" for d, _ in bulgu):
        return bulgu, {}
    if adlar.count(p["ad"]) > 1:
        H("ayni 'ad' planda birden cok kez (dosyalar ustune yazar)")
    if not 10 <= float(p["sure"]) <= 600:
        H(f"sure {p['sure']} sn, aralik 10-600")
    elif float(p["sure"]) > SURE_UYARI:
        U(f"sure {p['sure']} sn > {SURE_UYARI}: DiT adimi ~4 kat yavaslar, VRAM paylasimli bellege tasar (360 sn olcumu); ~600 sn'den uzun kosu Monitor ile")
    ct = len(tok(caption_metni(p)).input_ids)
    if ct > CAPTION_SINIR:
        H(f"caption+metas {ct} token > {CAPTION_SINIR}: fazlasi sondan kesilir (once bpm/ton/sure, sonra caption sonu); {ct - CAPTION_SINIR} token kisalt")
    elif ct > CAPTION_UYARI:
        U(f"caption+metas {ct} token, sinira {CAPTION_SINIR - ct} kaldi")
    if ",," in p["caption"] or "  " in p["caption"]:
        U("caption'da cift virgul ya da cift bosluk")
    soz = (p.get("lyrics") or "").strip()
    sozlu = bool(soz) and soz.lower() != "[instrumental]" and not p.get("instrumental", False)
    cap = p["caption"].lower()
    olcum = dict(caption_token=ct)
    if sozlu:
        dil = p.get("vocal_language", "unknown")
        if dil == "unknown":
            U("sozlu parca ama vocal_language yok/unknown (tr icin 'tr')")
        elif diller and dil not in diller:
            H(f"vocal_language '{dil}' paketin listesinde yok (ornek: tr, en, ja; acestep/constants.py VALID_LANGUAGES)")
        if ENSTRUMANTAL_DESEN.search(cap):
            H("caption 'no vocals/instrumental' diyor ama sozler var: celiski")
        lt = len(tok(f"# Languages\n{p.get('vocal_language', 'unknown')}\n\n# Lyric\n{soz}<|endoftext|>").input_ids)
        olcum["soz_token"] = lt
        if lt > SOZ_SINIR:
            H(f"sozler {lt} token > {SOZ_SINIR}: sonu kesilir")
        elif lt > SOZ_UYARI:
            U(f"sozler {lt} token, sinira yakin")
        bol = bolumler(soz)
        gerek = gereken_sure(p, bol)
        olcum["gereken_sn"] = gerek
        if gerek and gerek > float(p["sure"]):
            rap = bool(RAP_DESEN.search(cap)) or any(RAP_DESEN.search(ad) for ad, _ in bol)
            kaynak = "olculmus kaba kural: rap satiri 1,15 olcu" if rap else "olculmus kaba kural: sarki satiri 2 olcu"
            U(f"sozler ~{gerek} sn istiyor, sure {p['sure']} sn: son bolumler sikisir ya da soylenmez ({kaynak}; soz_zamani: true ile dogrula)")
        for ad, satirlar in bol:
            hs = [hece(s) for s in satirlar] if p.get("vocal_language") == "tr" else []  # hece sayaci Turkce sesliye gore
            if hs and (max(hs) > 16 or min(hs) < 3):
                U(f"[{ad}] satir hecesi {min(hs)}-{max(hs)} (kilavuz 6-10; bizde rapte 10-16 calisti)")
            elif hs and max(hs) - min(hs) > 5:
                U(f"[{ad}] satir uzunluklari dengesiz ({min(hs)}-{max(hs)} hece): ritim kayar")
            if len(ad) > 30 or ad.count("-") > 1:
                U(f"[{ad}] etiket uzun/ust uste: kisa tut ([Chorus - catchy] gibi)")
    else:
        if not re.search(r"\b(no vocals|instrumental)\b", cap):
            U("enstrumantal parca: caption'a 'no vocals' eklenmesi onerilir")
        if VOKAL_DESEN.search(cap.replace("no vocals", "").replace("wordless vocal", "")):
            U("enstrumantal parca ama caption'da vokal kelimesi var")
    if p.get("soz_zamani") and not sozlu:
        U("soz_zamani: true ama parca sozsuz")
    return bulgu, olcum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True); ap.add_argument("--yalniz", default=""); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.plan, encoding="utf-8") as f:
            plan = json.load(f)
        if not isinstance(plan.get("parcalar"), list) or not plan["parcalar"]:
            raise ValueError("'parcalar' bos olmayan bir liste olmali")
    except (OSError, ValueError, AttributeError) as e:  # JSONDecodeError da ValueError
        print(f"  HATA: plan okunamadi: {e}")
        print("DENETIM SONUC: 0 parca, 1 hata, 0 uyari"); sys.exit(2)
    secili = {x.strip() for x in a.yalniz.split(",") if x.strip()}
    parcalar = [p for p in plan["parcalar"] if not secili or (isinstance(p, dict) and p.get("ad") in secili)]
    adlar = [p.get("ad") if isinstance(p, dict) else None for p in plan["parcalar"]]
    if secili - set(adlar):
        print(f"  HATA: --yalniz planda olmayan ad: {', '.join(sorted(secili - set(adlar)))}")
        print("DENETIM SONUC: 0 parca, 1 hata, 0 uyari"); sys.exit(2)
    tok, diller = tokenizer(), gecerli_diller()
    hata, sonuc = 0, []
    for p in parcalar:
        bulgu, olcum = denetle(p, tok, adlar, diller)
        hata += sum(1 for d, _ in bulgu if d == "HATA")
        sonuc.append(dict(ad=p.get("ad") if isinstance(p, dict) else None, olcum=olcum, bulgu=[f"{d}: {m}" for d, m in bulgu]))
        if not a.json:
            print(f"DENETIM {p.get('ad') if isinstance(p, dict) else '?'}  {json.dumps(olcum, ensure_ascii=False)}")
            for d, m in bulgu:
                print(f"  {d}: {m}")
    if a.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(f"DENETIM SONUC: {len(parcalar)} parca, {hata} hata, "
          f"{sum(len(s['bulgu']) for s in sonuc) - hata} uyari", flush=True)
    sys.exit(2 if hata else 0)


if __name__ == "__main__":
    main()
