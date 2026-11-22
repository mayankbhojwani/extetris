@echo off
rem Windows: double-click this file to play ExTetris.
rem   play.bat --mode easy     play a chosen mode
rem   play.bat --catalogue     list every piece
rem   play.bat --check         check that Python, numpy and tkinter are ready
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 play.py %*
) else (
    python play.py %*
)
if errorlevel 1 (
    echo.
    echo ExTetris stopped with a problem, see above. If Python is missing,
    echo install it from https://www.python.org and tick "Add python.exe to PATH".
    pause
)
