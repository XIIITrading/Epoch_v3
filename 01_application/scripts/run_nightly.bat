@echo off
echo ============================================
echo  BUCKET B - NIGHTLY RUNNER
echo  Screener Pipeline (Seed 004)
echo ============================================
echo.
cd /d C:\XIIITradingSystems\Method_v1\01_application
python -m core.bucket_runner --bucket nightly
echo.
echo Exit code: %ERRORLEVEL%
pause
