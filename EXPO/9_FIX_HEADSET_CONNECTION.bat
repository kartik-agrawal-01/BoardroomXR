@echo off
setlocal EnableDelayedExpansion
title Fix headset connection
set "ADB=C:\Program Files\Unity\Hub\Editor\6000.5.4f1\Editor\Data\PlaybackEngines\AndroidPlayer\SDK\platform-tools\adb.exe"
echo   Restarting the adb service...
"%ADB%" kill-server >nul 2>&1
timeout /t 2 /nobreak >nul
"%ADB%" start-server
echo.
echo   Devices seen now:
"%ADB%" devices
echo.
echo   "unauthorized" : put the headset on and press ALLOW (tick "Always allow").
echo   nothing listed : try another USB port or cable; the cable must carry data.
echo   "offline"      : unplug, wait 5 s, plug back in, run this again.
echo   Developer mode must be ON in the Meta Horizon phone app.
pause
