@echo off
cd /d %~dp0
echo [HavenNest] Running apply_location_overrides...
echo Repo: %cd%
echo.

set REVIEW_CSV=location_audit.csv
set MODE_FLAG=

if not "%~1"=="" (
  set REVIEW_CSV=%~1
)

if /I "%~2"=="replace" (
  set MODE_FLAG=--replace
)
if /I "%~2"=="--replace" (
  set MODE_FLAG=--replace
)

if not exist "%REVIEW_CSV%" (
  if exist "location_audit.latest.csv" (
    set REVIEW_CSV=location_audit.latest.csv
  )
)

if not exist "%REVIEW_CSV%" (
  echo ERROR: review CSV not found.
  echo Expected: %cd%\location_audit.csv
  echo Or provide a path: apply_location_overrides.bat ^<path-to-csv^>
  echo Or place location_audit.latest.csv in repo root.
  echo.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python not found in PATH.
  echo Install Python or run from a terminal where python works.
  echo.
  pause
  exit /b 2
)

echo Using review CSV: %REVIEW_CSV%
if not "%MODE_FLAG%"=="" (
  echo Mode: replace (ONLY this CSV)
) else (
  echo Mode: merge (keep existing)
)
echo.
python tools\apply_location_overrides.py --review_csv "%REVIEW_CSV%" --overrides_json location_overrides.json %MODE_FLAG%
set EXITCODE=%ERRORLEVEL%
echo.
echo Exit code: %EXITCODE%
echo.
if not "%EXITCODE%"=="0" (
  echo ERROR: Failed to generate location_overrides.json
  pause
  exit /b %EXITCODE%
)

if exist "location_overrides.json" (
  echo OK: location_overrides.json updated.
) else (
  echo ERROR: location_overrides.json was not created.
)
echo.
pause
