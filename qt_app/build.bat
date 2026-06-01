@echo off
REM ============================================================
REM  Build SmacircleQt (Release) with Qt 6.10.1 MSVC + Ninja.
REM  Close any running SmacircleQt.exe first (it locks the exe).
REM ============================================================
setlocal

set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "QTDIR=C:\Qt\6.10.1\msvc2022_64"
set "CMAKE=C:\Qt\Tools\CMake_64\bin\cmake.exe"
set "NINJA=C:\Qt\Tools\Ninja\ninja.exe"
set "SRC=%~dp0."
set "BLD=%~dp0build"

echo === Initializing MSVC environment ===
call "%VCVARS%" >nul || goto :err

echo === Configuring ===
"%CMAKE%" -G Ninja -S "%SRC%" -B "%BLD%" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_PREFIX_PATH="%QTDIR%" ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" || goto :err

echo === Building ===
"%CMAKE%" --build "%BLD%" || goto :err

echo.
echo BUILD OK  ->  "%BLD%\SmacircleQt.exe"
echo (run deploy.bat once to bundle the Qt runtime, then run.bat)
exit /b 0

:err
echo.
echo *** BUILD FAILED (errorlevel %errorlevel%) ***
exit /b 1
