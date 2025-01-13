@echo off
:: Request admin privileges and run the Python script

:: Check if already elevated, else relaunch with admin privileges
echo Checking for admin rights...
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Already running with admin rights.
) else (
    echo Not running with admin rights. Relaunching with admin privileges...
    :: Relaunch the batch file with admin privileges
    powershell -Command "Start-Process cmd -ArgumentList '/c python \"C:\Users\jtann\OneDrive\Documents\tune up app\maintenance_script.py\"' -Verb RunAs"
    exit
)

:: If already elevated, just run the Python script
echo Running Python script...
python "C:\Users\jtann\OneDrive\Documents\tune up app\maintenance_script.py"

:: Prevent the command prompt from closing immediately
pause
