@echo off
REM ============================================================
REM  Bundle the Qt runtime (DLLs + QML plugins) next to the exe
REM  so it runs standalone / can be copied elsewhere.
REM  Run once after the first build (re-run if you add Qt modules).
REM ============================================================
setlocal
set "QTDIR=C:\Qt\6.10.1\msvc2022_64"
set "EXE=%~dp0build\SmacircleQt.exe"

if not exist "%EXE%" (
  echo Build first: "%EXE%" not found. Run build.bat
  exit /b 1
)

"%QTDIR%\bin\windeployqt.exe" --qmldir "%~dp0." --release "%EXE%" || exit /b 1
echo.
echo Deployed Qt runtime next to "%EXE%"
exit /b 0
