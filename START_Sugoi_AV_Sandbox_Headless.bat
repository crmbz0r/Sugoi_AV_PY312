@echo off
setlocal

set "TOOL_BAT=s:\Sugoi_AV_CUDA_Test\Code\Sugoi-Audio-Video-Translator-Headless.bat"

if not exist "%TOOL_BAT%" (
    echo [ERROR] Headless tool launcher not found:
    echo %TOOL_BAT%
    echo.
    echo Press any key to close...
    pause >nul
    exit /b 1
)

echo Starting Sugoi AV Sandbox (HEADLESS)...
call "%TOOL_BAT%" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Headless launcher exited with code %EXIT_CODE%.
    echo Press any key to close...
    pause >nul
)

endlocal
