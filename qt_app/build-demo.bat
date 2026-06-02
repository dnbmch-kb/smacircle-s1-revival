@echo off
REM ============================================================
REM  Build the NO-HARDWARE DEMO of SmacircleQt (simulated S1).
REM  Same as build.bat but with -DSMACIRCLE_DEMO=ON, into build-demo\,
REM  then bundles the Qt runtime and launches it. The demo flag is
REM  never set by release CI, so the simulation code never ships.
REM  Output: build-demo\smacircle-s1-revival-demo.exe
REM ============================================================
setlocal

set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "QTDIR=C:\Qt\6.10.1\msvc2022_64"
set "CMAKE=C:\Qt\Tools\CMake_64\bin\cmake.exe"
set "NINJA=C:\Qt\Tools\Ninja\ninja.exe"
set "SRC=%~dp0."
set "BLD=%~dp0build-demo"
set "EXE=%BLD%\smacircle-s1-revival-demo.exe"

echo === Initializing MSVC environment ===
call "%VCVARS%" >nul || goto :err

echo === Configuring (demo) ===
"%CMAKE%" -G Ninja -S "%SRC%" -B "%BLD%" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_PREFIX_PATH="%QTDIR%" ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" ^
  -DSMACIRCLE_DEMO=ON || goto :err

echo === Building (demo) ===
"%CMAKE%" --build "%BLD%" || goto :err

echo === Bundling Qt runtime ===
"%QTDIR%\bin\windeployqt.exe" --qmldir "%~dp0." --release "%EXE%" || goto :err

echo.
echo DEMO BUILD OK  ->  "%EXE%"
echo Launching... tap "Try demo - no bike needed".
start "" "%EXE%"
exit /b 0

:err
echo.
echo *** DEMO BUILD FAILED (errorlevel %errorlevel%) ***
exit /b 1
