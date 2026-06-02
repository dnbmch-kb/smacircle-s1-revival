@echo off
REM Launch the built app.
setlocal
set "EXE=%~dp0build\smacircle-s1-revival.exe"
if not exist "%EXE%" ( echo Build first with build.bat & exit /b 1 )
start "" "%EXE%"
