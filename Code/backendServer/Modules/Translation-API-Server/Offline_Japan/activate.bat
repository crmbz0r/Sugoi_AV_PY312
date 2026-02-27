@echo off
setlocal

color 9

set "MODEL_DIR=%~dp0Sugoi_Model\ct2Model"
set "MODEL_BIN=%MODEL_DIR%\model.bin"
set "MODEL_ARCHIVE_PART=%MODEL_DIR%\model.bin.7z.001"
set "DELETE_MODEL_ARCHIVE_PARTS=0"

if not exist "%MODEL_BIN%" (
	echo [INFO] model.bin not found. Checking for archive parts...
	if exist "%MODEL_ARCHIVE_PART%" (
		where 7z >nul 2>&1
		if errorlevel 1 (
			echo [ERROR] 7z not found in PATH. Install 7-Zip CLI or add 7z.exe to PATH.
			exit /b 1
		)

		echo [INFO] Extracting model from "%MODEL_ARCHIVE_PART%" ...
		7z x -y -o"%MODEL_DIR%" "%MODEL_ARCHIVE_PART%"

		if not exist "%MODEL_BIN%" (
			echo [ERROR] Extraction finished but model.bin is still missing.
			exit /b 1
		)

		echo [OK] model.bin restored.

		if "%DELETE_MODEL_ARCHIVE_PARTS%"=="1" (
			echo [INFO] Deleting archive parts to save disk space...
			del /q "%MODEL_DIR%\model.bin.7z.*" >nul 2>&1
		)
	) else (
		echo [ERROR] model.bin missing and no archive part found at:
		echo         "%MODEL_ARCHIVE_PART%"
		exit /b 1
	)
)

"../../../../Power-Source/Python312/python.exe" -s -E server.py