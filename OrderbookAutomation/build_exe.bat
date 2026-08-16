@echo off
REM ============================================================
REM  OrderbookAutomation - Build Script
REM
REM  Builds a standalone, directory-based ("--onedir") Windows
REM  executable using PyInstaller, from the OrderbookAutomation.spec
REM  file in this folder. Does not modify any business logic;
REM  this only packages the existing, already-tested application.
REM ============================================================

setlocal

cd /d "%~dp0"

echo.
echo === OrderbookAutomation build ===
echo.

REM ---- Step 1: Ensure PyInstaller is installed ----
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing build dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install build dependencies.
        exit /b 1
    )
)

REM ---- Step 2: Remove old build artifacts ----
echo Removing old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM ---- Step 3: Run PyInstaller ----
echo Running PyInstaller...
python -m PyInstaller OrderbookAutomation.spec
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See output above.
    exit /b 1
)

REM ---- Step 4: Create the expected client folder structure ----
echo Creating input/output/logs folders in the packaged application...
if not exist "dist\OrderbookAutomation\input"  mkdir "dist\OrderbookAutomation\input"
if not exist "dist\OrderbookAutomation\output" mkdir "dist\OrderbookAutomation\output"
if not exist "dist\OrderbookAutomation\logs"   mkdir "dist\OrderbookAutomation\logs"

echo.
echo === Build complete ===
echo Packaged application folder:
echo   %cd%\dist\OrderbookAutomation
echo.
echo Executable:
echo   %cd%\dist\OrderbookAutomation\OrderbookAutomation.exe
echo.

endlocal
