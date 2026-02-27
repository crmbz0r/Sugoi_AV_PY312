@echo off
setlocal

cd /d "%~dp0"

set "PY312_DIR=%~dp0..\..\..\Power-Source\Python312"
if exist "%PY312_DIR%\python.exe" (
	set "PATH=%PY312_DIR%;%PATH%"
)

if not exist "HF_CACHE" (
	mkdir "HF_CACHE"
)

if not exist "HF_CACHE\hub" (
	mkdir "HF_CACHE\hub"
)

if not exist "HF_CACHE\transformers" (
	mkdir "HF_CACHE\transformers"
)

set "HF_HOME=%CD%\HF_CACHE"
set "HUGGINGFACE_HUB_CACHE=%CD%\HF_CACHE\hub"
set "TRANSFORMERS_CACHE=%CD%\HF_CACHE\transformers"

if not exist "TEMP" (
	mkdir "TEMP"
)

set "TMP=%CD%\TEMP"
set "TEMP=%CD%\TEMP"

"../../../Power-Source/Python312/python.exe" -s -E transcriptionServer.py

endlocal
