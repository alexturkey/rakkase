"""ACE-Step venv'inin uv baslaticisi (Scripts/python.exe) 2026-11-04'te 'uv trampoline failed to spawn' verdi; taban Python saglam.
Kok neden (2026-11-05): exe icine gomulu yol eski klasor adini tasiyordu; `uv venv --allow-existing` ile onarildi (KURULUM_DEFTERI 6.5).
Bu baslatici taban Python'a venv paketlerini tanitip betigi calistirir (venv'e dokunmaz); bellek_izle.ps1 'calistir.py' adina bakar.
Kullanim: rakkase.py uzerinden (python rakkase.py uret ...); dogrudan: <venv python> calistir.py --plan ... (BETIK varsayilan dokum_muzik.py)
"""
import glob
import json
import os
import runpy
import site
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(KOK, "..", "ayarlar.json"), encoding="utf-8") as _f:
    _ayar = json.load(_f)
VENV = os.path.expandvars(os.environ.get("RAKKASE_VENV") or _ayar.get("venv") or os.path.join(_ayar["ace_kok"], ".venv"))  # K20
for _sp in [os.path.join(VENV, "Lib", "site-packages")] + glob.glob(os.path.join(VENV, "lib", "python*", "site-packages")):
    if os.path.isdir(_sp):
        site.addsitedir(_sp)
BETIK = os.path.join(KOK, os.environ.get("BETIK", "dokum_muzik.py"))
sys.argv = [BETIK] + sys.argv[1:]
runpy.run_path(BETIK, run_name="__main__")
