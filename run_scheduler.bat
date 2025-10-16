@echo off
REM Windows Trial Scheduler Execution Script
REM This batch file runs the trial scheduler with proper error handling

echo Starting Windows Trial Scheduler...
echo Execution Time: %date% %time%

REM Change to the script directory
cd /d "%~dp0"

REM Run the Python script
python trial_scheduler.py

REM Check exit code
if %errorlevel% equ 0 (
    echo Trial Scheduler completed successfully
) else (
    echo Trial Scheduler failed with error code %errorlevel%
    echo Check logs/trial_scheduler.log for details
)

echo Execution completed at: %date% %time%
pause
