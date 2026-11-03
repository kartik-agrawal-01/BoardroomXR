@echo off
setlocal EnableDelayedExpansion
title BUILD and TEST BoardroomXR v6  (close the Unity editor first)
set "UNITY=C:\Program Files\Unity\Hub\Editor\6000.5.4f1\Editor\Unity.exe"
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"
set "TOOLS=%PROJ%\Tools"
set "TLOG=%TOOLS%\test_v6.log"
set "TRES=%TOOLS%\test_results_v6.xml"
set "BLOG=%TOOLS%\build_v6.log"
set "SUM=%TOOLS%\v6_summary.txt"
set "APK=%USERPROFILE%\BoardroomXR_v6.apk"
mkdir "%TOOLS%" 2>nul

if exist "%PROJ%\Temp\UnityLockfile" (
  echo   The project looks locked - is the Unity editor open? Close Unity and run this again.
  echo   If Unity is definitely closed, delete %PROJ%\Temp\UnityLockfile
  pause
  exit /b 1
)
if not exist "%UNITY%" ( echo   Unity 6000.5.4f1 not found at %UNITY% & pause & exit /b 1 )

echo BoardroomXR v6 build and test, %DATE% %TIME%> "%SUM%"
del "%TRES%" 2>nul
echo.
echo   [1/2] Compiling and running all PlayMode tests. About 5-10 minutes...
"%UNITY%" -batchmode -projectPath "%PROJ%" -runTests -testPlatform PlayMode -testResults "%TRES%" -logFile "%TLOG%"

if not exist "%TRES%" (
  echo   NO TEST RESULTS - most likely a compile error. Errors from the log:
  echo COMPILE OR TEST RUN FAILED - no results file>> "%SUM%"
  findstr /c:"error CS" "%TLOG%"
  findstr /c:"error CS" "%TLOG%" >> "%SUM%"
  echo.
  echo   Tell Claude: "build failed" - it will read Tools\test_v6.log
  pause
  exit /b 1
)

powershell -NoProfile -Command "$x=[xml](Get-Content '%TRES%'); $r=$x.'test-run'; $s='TESTS total={0} passed={1} failed={2} skipped={3}' -f $r.total,$r.passed,$r.failed,$r.skipped; Write-Host ('  '+$s); Add-Content '%SUM%' $s; $x.SelectNodes('//test-case[@result=''Failed'']') | ForEach-Object { $l='  FAILED: '+$_.fullname+' :: '+($_.failure.message.'#cdata-section' -replace '\s+',' '); Write-Host $l; Add-Content '%SUM%' $l }"

echo.
echo   [2/2] Building the Quest APK (IL2CPP, 10-25 minutes)...
del "%APK%" 2>nul
"%UNITY%" -batchmode -quit -projectPath "%PROJ%" -buildTarget Android -executeMethod BoardroomXR.EditorTools.BoardroomBuild.BuildApk -logFile "%BLOG%"
if not exist "%APK%" (
  echo   BUILD FAILED. Last lines of the log:
  echo BUILD FAILED>> "%SUM%"
  powershell -NoProfile -Command "Get-Content '%BLOG%' -Tail 25"
  echo   IL2CPP sometimes fails once with an AccessViolation on this laptop - just run this again.
  pause
  exit /b 1
)

copy /y "%APK%" "%PROJ%\EXPO\BoardroomXR_v6.apk" >nul
powershell -NoProfile -Command "$h=(Get-FileHash '%PROJ%\EXPO\BoardroomXR_v6.apk' -Algorithm SHA256).Hash; Set-Content '%PROJ%\EXPO\BoardroomXR_v6.apk.sha256' ($h+'  BoardroomXR_v6.apk'); Add-Content '%SUM%' ('BUILD OK sha256='+$h); Write-Host ('  APK sha256 '+$h)"
echo.
echo   BUILD OK: EXPO\BoardroomXR_v6.apk
echo   Next: plug in the headset and run EXPO\1_INSTALL_v6.bat
echo   Tell Claude "built" - it will read Tools\v6_summary.txt
pause
