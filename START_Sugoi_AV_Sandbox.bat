@echo off
setlocal

set "TOOL_BAT=s:\Sugoi_AV_CUDA_Test\Code\Sugoi-Audio-Video-Translator.bat"

if not exist "%TOOL_BAT%" (
    echo [ERROR] Tool launcher not found:
    echo %TOOL_BAT%
    echo.
    echo Press any key to close...
    pause >nul
    exit /b 1
)

echo Starting Sugoi AV Sandbox...
call "%TOOL_BAT%" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Launcher exited with code %EXIT_CODE%.
    echo Press any key to close...
    pause >nul
)

endlocal
