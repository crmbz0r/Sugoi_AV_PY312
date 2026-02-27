REM Assign the first parameter to a variable
set translator_name=%1

cd backendServer
cd Modules
cd Translation-API-Server

@REM "../../../Power-Source/Python39/python.exe" -s -E main.py
@REM call activate.bat

cd %translator_name%
call activate.bat