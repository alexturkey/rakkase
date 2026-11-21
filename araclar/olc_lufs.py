"""Aday WAV'larin suresini ve tumlesik LUFS / gercek tepe degerini ffmpeg loudnorm ile olcer; olcum.json yazar."""
import glob
import json
import os
import re
import subprocess
import sys

KLASOR = os.path.dirname(os.path.abspath(__file__))
GIZLI = 0x08000000  # CREATE_NO_WINDOW


def olc(yol):
    p = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-i", yol, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=GIZLI,
    )
    j = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    q = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", yol],
        capture_output=True, text=True, creationflags=GIZLI,
    )
    return {"dosya": os.path.basename(yol), "sure_sn": round(float(q.stdout.strip()), 2),
            "lufs": float(j["input_i"]), "tepe_dbtp": float(j["input_tp"]), "lra": float(j["input_lra"])}


desen = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KLASOR, "*.wav")
sonuc = [olc(f) for f in sorted(glob.glob(desen))]
for s in sonuc:
    print(f"{s['dosya']}: {s['sure_sn']} sn, {s['lufs']} LUFS, tepe {s['tepe_dbtp']} dBTP, LRA {s['lra']}")
json.dump(sonuc, open(os.path.join(KLASOR, "olcum.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
