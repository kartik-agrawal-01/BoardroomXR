@echo off
setlocal EnableDelayedExpansion
set "EXPO=%~dp0"
if "%EXPO:~-1%"=="\" set "EXPO=%EXPO:~0,-1%"
set "ADB=C:\Program Files\Unity\Hub\Editor\6000.5.4f1\Editor\Data\PlaybackEngines\AndroidPlayer\SDK\platform-tools\adb.exe"
set "PKG=com.kartikagrawal.boardroomxr"
set "ACTIVITY=com.unity3d.player.UnityPlayerGameActivity"
set "REMOTE=/sdcard/Android/data/%PKG%/files"
if not exist "%ADB%" ( echo   adb not found: %ADB% & echo   Run CHECK_SETUP.bat first. & pause & exit /b 1 )
"%ADB%" start-server >nul 2>&1
set "SERIAL="
for /f "skip=1 tokens=1,2" %%A in ('"%ADB%" devices') do if "%%B"=="device" if not defined SERIAL set "SERIAL=%%A"
if not defined SERIAL (
  echo.
  echo   NO HEADSET FOUND.
  echo   1. Plug the USB-C cable into the headset and the laptop.
  echo   2. Put the headset on and press ALLOW on the "Allow USB debugging" prompt.
  echo   3. Still nothing? Run 9_FIX_HEADSET_CONNECTION.bat
  pause
  exit /b 1
)
set "A="%ADB%" -s !SERIAL!"
title Keep headset awake
echo   Disabling the proximity sensor so the app keeps running when the
echo   headset is taken off and handed to the next person.
!A! shell am broadcast -a com.oculus.vrpowermanager.prox_close >nul
echo   Done. Run KEEP_AWAKE_OFF.bat after the expo (saves battery).
timeout /t 5
