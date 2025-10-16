# Windows Trial Scheduler PowerShell Execution Script
# This PowerShell script runs the trial scheduler with enhanced error handling and logging

param(
    [switch]$Verbose,
    [string]$LogFile = "logs\execution.log"
)

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Create logs directory if it doesn't exist
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force
}

# Function to write log
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Start execution
Write-Log "Starting Windows Trial Scheduler..." "INFO"
Write-Log "Script Directory: $ScriptDir" "INFO"
Write-Log "Python Version: $(python --version)" "INFO"

try {
    # Check if Python is available
    $PythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python is not installed or not in PATH"
    }
    Write-Log "Python found: $PythonVersion" "INFO"
    
    # Check if requirements are installed
    Write-Log "Checking dependencies..." "INFO"
    python -c "import requests, sqlalchemy, psycopg2" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Installing dependencies..." "INFO"
        pip install -r requirements.txt
    }
    
    # Run the trial scheduler
    Write-Log "Executing trial scheduler..." "INFO"
    $StartTime = Get-Date
    
    python trial_scheduler.py
    
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Trial Scheduler completed successfully in $($Duration.TotalSeconds) seconds" "SUCCESS"
    } else {
        Write-Log "Trial Scheduler failed with exit code $LASTEXITCODE" "ERROR"
        Write-Log "Check logs/trial_scheduler.log for details" "ERROR"
    }
    
} catch {
    Write-Log "Error executing trial scheduler: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

Write-Log "Execution completed" "INFO"
