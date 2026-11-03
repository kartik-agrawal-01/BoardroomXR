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
title Roll back to v5
set "APK=%EXPO%\BoardroomXR_v5.apk"
if not exist "%APK%" ( echo   %APK% not found. & pause & exit /b 1 )
echo   Use this only if v6 misbehaves. Installs the old v5 (profiles kept).
choice /c YN /m "  Install v5 now"
if errorlevel 2 exit /b 0
!A! install -r -d "%APK%"
if errorlevel 1 (
  echo   Direct downgrade refused. Uninstalling first ^(this deletes profiles^)...
  !A! uninstall %PKG%
  !A! install "%APK%"
)
!A! shell am start -n %PKG%/%ACTIVITY% >nul
echo   v5 installed and started. Note: START_EXPO.bat expects v6 and may offer to update it.
pause
