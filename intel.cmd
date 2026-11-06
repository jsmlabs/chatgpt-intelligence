@echo off
setlocal
cd /d "%~dp0"
echo.
echo ChatGPT Intelligence - Windows launcher
echo [1] Start ChatGPT tunnel
echo [2] Status
echo [3] Doctor
echo [4] Local MCP test
echo [5] Ollama model list (optional)
echo [6] Locate tunnel-client executable
echo [0] Exit
set /p "choice=Select action [1]: "
if "%choice%"=="" set "choice=1"
if "%choice%"=="0" exit /b 0
if "%choice%"=="1" set "action=Start"
if "%choice%"=="2" set "action=Status"
if "%choice%"=="3" set "action=Doctor"
if "%choice%"=="4" set "action=Test"
if "%choice%"=="5" set "action=Ollama"
if "%choice%"=="6" set "action=Locate"
if not defined action (
  echo Invalid choice.
  pause
  exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\intel.ps1" -Action "%action%"
set "result=%ERRORLEVEL%"
echo.
if not "%result%"=="0" echo Action exited with code %result%.
pause
exit /b %result%
