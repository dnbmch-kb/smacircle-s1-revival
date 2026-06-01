@echo off
REM Launch the built app.
setlocal
set "EXE=%~dp0build\SmacircleQt.exe"
if not exist "%EXE%" ( echo Build first with build.bat & exit /b 1 )
start "" "%EXE%"
