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

for /f %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Content -Raw '..\..\..\User-Settings.json' | ConvertFrom-Json).Sugoi_Audio_Video_Translator.transcription_server_port_number"') do set "TRANSCRIPTION_PORT=%%P"

set "TRANSCRIPTION_LISTENING="
if defined TRANSCRIPTION_PORT (
	for /f %%L in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%TRANSCRIPTION_PORT%; (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { 'YES' })"') do set "TRANSCRIPTION_LISTENING=%%L"
)

if not "%TRANSCRIPTION_LISTENING%"=="YES" (
	echo [INFO] Transcription server not listening on port %TRANSCRIPTION_PORT%. Starting it now...
	start "Sugoi AV Transcription Server" /min cmd /k "activateTranscriptionServer.bat"
	if defined TRANSCRIPTION_PORT (
		powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%TRANSCRIPTION_PORT%; $deadline=(Get-Date).AddSeconds(180); while((Get-Date) -lt $deadline){ if(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue){ exit 0 }; Start-Sleep -Seconds 2 }; exit 1"
		if errorlevel 1 (
			echo [ERROR] Transcription server did not start on port %TRANSCRIPTION_PORT%.
			echo Press any key to close this window...
			pause >nul
			exit /b 1
		)
	)
)

if exist "../../../Power-Source/Python312/python.exe" (
	"../../../Power-Source/Python312/python.exe" -s -E -c "import srt, requests" >nul 2>nul
	if not errorlevel 1 (
		set "PROCESS_PY=../../../Power-Source/Python312/python.exe"
	)
)

"%PROCESS_PY%" -s -E process_headless.py %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
	echo.
	echo [ERROR] Headless processor exited with code %EXIT_CODE%.
	echo Press any key to close this window...
	pause >nul
)

endlocal
