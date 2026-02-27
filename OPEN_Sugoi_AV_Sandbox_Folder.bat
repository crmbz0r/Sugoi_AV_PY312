@echo off
setlocal

set "TOOL_DIR=s:\Sugoi_AV_CUDA_Test\Code\backendServer\Program-Backend\Sugoi-Audio-Video-Translator"

if not exist "%TOOL_DIR%" (
    echo [ERROR] Folder not found:
    echo %TOOL_DIR%
    echo.
    echo Press any key to close...
    pause >nul
    exit /b 1
)

start "" "%TOOL_DIR%"

endlocal
