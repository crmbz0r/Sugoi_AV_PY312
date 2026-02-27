@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"
set "SETTINGS_FILE=%SCRIPT_DIR%User-Settings.json"

set "PY312_DIR=%~dp0Power-Source\Python312"
if exist "%PY312_DIR%\python.exe" (
	set "PATH=%PY312_DIR%;%PATH%"
)

for /f %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Content -Raw '%SETTINGS_FILE%' | ConvertFrom-Json).Sugoi_Audio_Video_Translator.transcription_server_port_number"') do set "TRANSCRIPTION_PORT=%%P"
for /f %%T in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Content -Raw '%SETTINGS_FILE%' | ConvertFrom-Json).Translation_API_Server.current_translator"') do set "CURRENT_TRANSLATOR=%%T"
for /f %%Q in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$cfg=(Get-Content -Raw '%SETTINGS_FILE%' | ConvertFrom-Json); $name=$cfg.Translation_API_Server.current_translator; $translatorNode=$cfg.Translation_API_Server.PSObject.Properties[$name].Value; $translatorNode.HTTP_port_number"') do set "TRANSLATION_PORT=%%Q"

if defined TRANSCRIPTION_PORT (
	powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%TRANSCRIPTION_PORT%; Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
)

if defined TRANSLATION_PORT (
	powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%TRANSLATION_PORT%; Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
)

if defined CURRENT_TRANSLATOR (
	start "Sugoi Translation API Server" /min cmd /k "Translation-API-Server.bat %CURRENT_TRANSLATOR%"
)

cd /d "%SCRIPT_DIR%backendServer\Program-Backend\Sugoi-Audio-Video-Translator"

start "Sugoi AV Transcription Server" /min cmd /k "activateTranscriptionServer.bat"
start "Sugoi AV Processor Headless" cmd /k "activate_processor_headless.bat %*"

popd
endlocal
