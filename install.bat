@echo off
setlocal EnableDelayedExpansion
title Gurukul CMS — Windows Installer

echo.
echo  ============================================================
echo   Gurukul CMS — Windows Installer
echo  ============================================================
echo.

:: ── Check Python is installed ────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python 3.11 from https://www.python.org/downloads/
    echo  During install, check "Add Python to PATH" then re-run this script.
    echo.
    pause
    exit /b 1
)

:: Check Python version is 3.11
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if not "!PYMAJOR!"=="3" (
    echo  [ERROR] Python 3.11 is required. Found: !PYVER!
    pause
    exit /b 1
)
if not "!PYMINOR!"=="11" (
    echo  [WARNING] Python 3.11 recommended. Found: !PYVER!
    echo  Continuing anyway — press Ctrl+C to abort or any key to continue.
    pause >nul
)

echo  [OK] Python !PYVER! found.
echo.

:: ── Create virtual environment ───────────────────────────────────────────────
if exist venv (
    echo  [INFO] Virtual environment already exists, skipping creation.
) else (
    echo  [STEP 1] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
)
echo.

:: ── Activate venv ────────────────────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.
echo.

:: ── Upgrade pip ──────────────────────────────────────────────────────────────
echo  [STEP 2] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  [OK] pip upgraded.
echo.

:: ── Install dependencies ─────────────────────────────────────────────────────
echo  [STEP 3] Installing dependencies (this may take 3-5 minutes)...
pip install -r requirements_windows.txt
if errorlevel 1 (
    echo.
    echo  [ERROR] Dependency installation failed.
    echo  Try running manually:
    echo    venv\Scripts\activate
    echo    pip install -r requirements_windows.txt
    pause
    exit /b 1
)
echo.
echo  [OK] All dependencies installed.
echo.

:: ── Copy existing database if provided ──────────────────────────────────────
set DB_DEST=%USERPROFILE%\Documents\GurukulCMS
if not exist "%DB_DEST%" mkdir "%DB_DEST%"

if exist tuition_cms.db (
    echo  [STEP 4] Copying existing database to %DB_DEST%\tuition_cms.db ...
    copy /Y tuition_cms.db "%DB_DEST%\tuition_cms.db" >nul
    echo  [OK] Database copied.
    echo.
) else (
    echo  [INFO] No tuition_cms.db found in project folder.
    echo         A fresh database will be created on first run.
    echo.
)

:: ── Ask user: run dev or build exe ───────────────────────────────────────────
echo  ============================================================
echo   What would you like to do?
echo.
echo   [1] Run the app now (development mode)
echo   [2] Build GurukuCMS.exe (takes 5-10 minutes)
echo   [3] Exit
echo  ============================================================
echo.
set /p CHOICE= Enter 1, 2, or 3: 

if "!CHOICE!"=="1" goto RUN_DEV
if "!CHOICE!"=="2" goto BUILD_EXE
goto END

:: ── Run in development mode ──────────────────────────────────────────────────
:RUN_DEV
echo.
echo  Starting Gurukul CMS...
python main.py
goto END

:: ── Build the exe ────────────────────────────────────────────────────────────
:BUILD_EXE
echo.
echo  [STEP 4] Building GurukuCMS.exe with PyInstaller...
echo  This will take 5-10 minutes. Do not close this window.
echo.

:: Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

pyinstaller gurukul.spec
if errorlevel 1 (
    echo.
    echo  [ERROR] PyInstaller build failed.
    echo  Check the output above for the exact error.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   BUILD SUCCESSFUL
echo   Executable: dist\GurukuCMS.exe
echo.
echo   To distribute: copy dist\GurukuCMS.exe anywhere.
echo   Database is stored at:
echo   %USERPROFILE%\Documents\GurukulCMS\tuition_cms.db
echo  ============================================================
echo.

:: Offer to run the exe immediately
set /p RUNEXE= Run GurukuCMS.exe now? (y/n): 
if /i "!RUNEXE!"=="y" start "" "dist\GurukuCMS.exe"

:END
echo.
echo  Done.
pause
