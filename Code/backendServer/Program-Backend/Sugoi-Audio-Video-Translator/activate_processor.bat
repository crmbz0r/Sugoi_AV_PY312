@echo off
setlocal

cd /d "%~dp0"

set "PY312_DIR=%~dp0..\..\..\Power-Source\Python312"
set "PY39_DIR=%~dp0..\..\..\Power-Source\Python39"
if exist "%PY312_DIR%\python.exe" (
	set "PATH=%PY312_DIR%;%PATH%"
)
if exist "%PY39_DIR%\python.exe" (
	set "PATH=%PY39_DIR%;%PATH%"
)

if not exist "TEMP" (
	mkdir "TEMP"
)

set "TMP=%CD%\TEMP"
set "TEMP=%CD%\TEMP"

color 6
set "PROCESS_PY=../../../Power-Source/Python39/python.exe"

if exist "../../../Power-Source/Python312/python.exe" (
	"../../../Power-Source/Python312/python.exe" -s -E -c "import tkinter" >nul 2>nul
	if not errorlevel 1 (
		set "PROCESS_PY=../../../Power-Source/Python312/python.exe"
	)
)

"%PROCESS_PY%" -s -E process.py %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
	echo.
	echo [ERROR] Processor exited with code %EXIT_CODE%.
	echo Press any key to close this window...
	pause >nul
)

endlocal