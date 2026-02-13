@echo off
title DOW AI Trading Assistant
color 0A

:start
cd /d C:\XIIITradingSystems\Epoch
call venv\Scripts\activate.bat 2>nul

:menu
cls
echo.
echo  ======================================================================
echo    DOW AI TRADING ASSISTANT
echo  ======================================================================
echo.
echo    ENTRY ANALYSIS:
echo      entry [TICKER] [long/short] [primary/secondary]
echo.
echo    Examples:
echo      entry NVDA long secondary
echo      entry TSLA short primary
echo.
echo    For HISTORICAL analysis, use -d flag:
echo      entry MSFT long primary -d 2024-12-03-10:30
echo      (Format: YYYY-MM-DD-HH:MM with dashes, no spaces)
echo.
echo    EXIT ANALYSIS:
echo      exit [TICKER] [sell/cover] [primary/secondary]
echo.
echo    The tool auto-calculates the EPCH model (01/02/03/04) based on
echo    zone direction and trade direction.
echo.
echo    Type 'quit' to exit
echo  ======================================================================
echo.

set /p "usercmd=dow> "
if /i "%usercmd%"=="quit" goto end
if /i "%usercmd%"=="q" goto end
if "%usercmd%"=="" goto menu

echo.
python 04_dow_ai\main.py %usercmd%
echo.
echo ----------------------------------------------------------------------
pause
goto menu

:end
echo.
echo Goodbye!
timeout /t 2 >nul
