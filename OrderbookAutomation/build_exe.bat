@echo off
REM ============================================================
REM  OrderbookAutomation - PRODUCTION BUILD SCRIPT
REM
REM  Builds a standalone, directory-based ("--onedir") Windows
REM  executable with PyInstaller and stages a clean client
REM  release folder:
REM
REM      release\
REM        +-- OrderbookAutomation.exe   (+ runtime libraries)
REM        +-- input\                    (empty - client drops files here)
REM        +-- output\                   (empty - POB.xlsx is written here)
REM        +-- logs\                     (empty - technical logs)
REM
REM  Does not modify business logic; this only packages the
REM  existing, already-tested application.
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo === OrderbookAutomation production build ===
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
if exist "build"   rmdir /s /q "build"
if exist "dist"    rmdir /s /q "dist"
if exist "release" rmdir /s /q "release"

REM ---- Step 3: Run PyInstaller ----
echo Running PyInstaller...
python -m PyInstaller OrderbookAutomation.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

REM ---- Step 4: Stage the client release folder ----
echo Staging release folder...
mkdir "release"
xcopy /e /i /q /y "dist\OrderbookAutomation" "release" >nul
if errorlevel 1 (
    echo.
    echo ERROR: Failed to stage release folder.
    exit /b 1
)

REM Client-facing working folders. These MUST ship empty: no input
REM workbooks and no generated output are ever packaged.
mkdir "release\input"  2>nul
mkdir "release\output" 2>nul
mkdir "release\logs"   2>nul

REM ---- Step 5: Safety sweep ----
REM Guarantee no development artifacts leaked into the release.
if exist "release\tests"      rmdir /s /q "release\tests"
if exist "release\__pycache__" rmdir /s /q "release\__pycache__"
del /s /q "release\*.py"  >nul 2>&1
del /s /q "release\*.pyc" >nul 2>&1
del /s /q "release\*.spec" >nul 2>&1

echo.
echo === BUILD COMPLETE ===
echo.
echo   EXE:      %~dp0release\OrderbookAutomation.exe
echo   Release:  %~dp0release\
echo.
echo Client usage:
echo   1. Copy the 'release' folder anywhere on Windows.
echo   2. Put the daily Excel files into 'input'.
echo   3. Run OrderbookAutomation.exe
echo   4. Collect 'output\POB.xlsx'
echo.

endlocal
