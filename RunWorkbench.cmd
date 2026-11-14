@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Install first: python -m venv .venv ^&^& .venv\Scripts\python -m pip install -e ".[gui,dev]" 1>&2
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -m staubli_workbench.cli %*
exit /b %errorlevel%
