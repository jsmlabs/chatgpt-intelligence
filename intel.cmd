@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%~dp0intel.py" %*
) else (
  python "%~dp0intel.py" %*
)
exit /b %ERRORLEVEL%
