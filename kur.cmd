@echo off
rem Rakkase kur.cmd. EN: double-click, or run in cmd, to install (ACE-Step clone, uv environment, models about 6 GB with sha256 checks, settings, plan check). Extra flags go to scripts\kur.ps1, e.g. kur.cmd -Kuru (dry run: reports only, changes nothing, no network).
rem TR: cift tikla ya da cmd icinde calistir; kurulum yapar (ACE-Step klonu, uv ortami, yaklasik 6 GB model sha256 dogrulamali, ayarlar, plan denetimi). Ek bayraklar scripts\kur.ps1 dosyasina gider, orn. kur.cmd -Kuru (kuru calisma: yalniz rapor, hicbir sey degistirmez, ag yok).
rem Exit codes / cikis kodlari: 0 ok, 1 error, 2 input needed (git or uv missing, bad ayarlar.json), 3 hardware or disk, 4 stopped. Codes: docs\SIK_HATALAR.md
rem Env: RK_POWERSHELL (path to powershell.exe if it is not on PATH), RK_NO_PAUSE=1 (never wait for a key), RK_PAUSE=1 (always wait), RK_UV (uv.exe path).
rem No labels and no multi-line blocks on purpose: this file still works if a download converted it to LF line endings.
setlocal
for /f "tokens=2 delims=:" %%a in ('chcp') do set "RK_ESKI_CP=%%a"
chcp 65001 >nul
cd /d "%~dp0"
if not defined RK_POWERSHELL set "RK_POWERSHELL=powershell.exe"
echo Rakkase kur.cmd: starting scripts\kur.ps1 / scripts\kur.ps1 basliyor. About 6 GB model download plus the Python environment; safe to re-run, it continues where it stopped / yaklasik 6 GB model indirmesi ve Python ortami; tekrar calistirmak guvenli, kaldigi yerden surer. %*
call "%RK_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kur.ps1" %*
set "RK_KOD=%ERRORLEVEL%"
echo.
echo Exit code / cikis kodu: %RK_KOD%  (0 = ok / tamam, 2 = git or uv missing or bad settings / git ya da uv yok ya da ayar bozuk, 3 = hardware or disk not enough / donanim ya da disk yetersiz, 4 = stopped / durduruldu)
echo Codes and fixes / kodlar ve cozumler: docs\SIK_HATALAR.md
rem Double-click detection runs BEFORE the code page is restored: on a non-Turkish OEM code page the Turkish letters in the path no longer match.
set "RK_CIFT="
echo %cmdcmdline% | "%SystemRoot%\System32\find.exe" /i "%~f0" >nul && set "RK_CIFT=1"
chcp %RK_ESKI_CP% >nul
if "%RK_PAUSE%"=="1" set "RK_CIFT=1"
if "%RK_NO_PAUSE%"=="1" set "RK_CIFT="
if defined RK_CIFT pause
endlocal & exit /b %RK_KOD%
