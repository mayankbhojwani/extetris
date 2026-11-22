@echo off
rem Windows: double-click this file to open the Variant Designer.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 design.py %*
) else (
    python design.py %*
)
if errorlevel 1 (
    echo.
    echo The Variant Designer stopped with a problem, see above. If Python is missing,
    echo install it from https://www.python.org and tick "Add python.exe to PATH".
    pause
)
