@echo off
rem Rakkase uret.cmd. EN: drag a plan .json file onto this file (or: uret.cmd plan.json) to generate it. With no argument it generates the safe example ornekler\sozsuz_fon_ninni.json (instrumental, 96 s of music; about 3 to 3.5 minutes in total on a GTX 1050 Ti: model load about 2 min plus about 63-75 s for a 100 s track [measured by the authors, docs\OLCUMLER.md]). The files are written under uretimler\ (see docs\KULLANIM.md).
rem TR: plan .json dosyasini bu dosyanin ustune surukle (ya da: uret.cmd plan.json): uretir. Arguman yoksa guvenli ornek plani uretir: ornekler\sozsuz_fon_ninni.json (enstrumantal, 96 sn; GTX 1050 Ti'de toplam yaklasik 3-3,5 dk). Dosyalar uretimler\ altina yazilir (docs\KULLANIM.md).
rem Exit codes / cikis kodlari (python rakkase.py uret): 0 ok, 2 plan error or engine did not start, 3 a track failed, 4 RAM guard stopped, 5 done but mp3/archive failed, 6 ayarlar.json missing or wrong. Codes: docs\SIK_HATALAR.md
rem Env: RK_PYTHON (python executable, default: the ACE-Step environment python.exe named by ayarlar.json, so no system Python is needed; if that is missing: python), RK_NO_PAUSE=1, RK_PAUSE=1 (see kur.cmd). No labels and no multi-line blocks on purpose (LF-safe).
setlocal
for /f "tokens=2 delims=:" %%a in ('chcp') do set "RK_ESKI_CP=%%a"
chcp 65001 >nul
cd /d "%~dp0"
if not defined RK_PYTHON for /f "usebackq delims=" %%p in (`powershell.exe -NoProfile -Command "try { $a = Get-Content -Raw -Encoding UTF8 ayarlar.json | ConvertFrom-Json; $v = if ($a.venv) { $a.venv } else { Join-Path $a.ace_kok '.venv' }; $p = Join-Path $v 'Scripts\python.exe'; if (Test-Path -LiteralPath $p) { $p } } catch {}"`) do set "RK_PYTHON=%%p"
if not defined RK_PYTHON set "RK_PYTHON=python"
set "RK_KOD=0"
set "RK_CIFT="
echo %cmdcmdline% | "%SystemRoot%\System32\find.exe" /i "%~f0" >nul && set "RK_CIFT=1"
if "%~1"=="" echo Rakkase uret.cmd: no plan given, generating the example ornekler\sozsuz_fon_ninni.json / plan verilmedi, ornek plan uretiliyor.
if "%~1"=="" call "%RK_PYTHON%" -X utf8 rakkase.py uret --plan ornekler\sozsuz_fon_ninni.json
if "%~1"=="" set "RK_KOD=%ERRORLEVEL%"
if not "%~1"=="" if exist "%~1" echo Rakkase uret.cmd: generating / uretiliyor: %~1
if not "%~1"=="" if exist "%~1" call "%RK_PYTHON%" -X utf8 rakkase.py uret --plan "%~1"
if not "%~1"=="" if exist "%~1" set "RK_KOD=%ERRORLEVEL%"
if not "%~1"=="" if not exist "%~1" echo File not found / dosya bulunamadi: %~1 . Usage / kullanim: uret.cmd plan.json
if not "%~1"=="" if not exist "%~1" set "RK_KOD=1"
echo.
echo Exit code / cikis kodu: %RK_KOD%  (0 = ok / tamam, 2 = plan error / plan hatasi, 3 = a track failed / bir parca basarisiz, 4 = RAM guard / RAM bekcisi, 5 = mp3 or archive failed / mp3 ya da arsiv basarisiz, 6 = ayarlar.json missing or wrong / ayarlar.json eksik ya da yanlis)
echo Codes and fixes / kodlar ve cozumler: docs\SIK_HATALAR.md
chcp %RK_ESKI_CP% >nul
if "%RK_PAUSE%"=="1" set "RK_CIFT=1"
if "%RK_NO_PAUSE%"=="1" set "RK_CIFT="
if defined RK_CIFT pause
endlocal & exit /b %RK_KOD%
