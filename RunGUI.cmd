@echo off
setlocal
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
  echo Install the gui extra in .venv first. 1>&2
  exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" -m staubli_workbench.gui
