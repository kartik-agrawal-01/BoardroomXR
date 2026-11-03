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
title Reconnect dashboard
echo   Re-creating the USB link for the dashboard (port 8080)...
!A! forward --remove-all >nul 2>&1
!A! forward tcp:8080 tcp:8080
if errorlevel 1 ( echo   Forward failed. Is the app running? Try 2_RESTART_APP.bat & pause & exit /b 1 )
start "" http://localhost:8080
echo   Dashboard opened. If it says "no data", the app is not running on the headset.
timeout /t 5
