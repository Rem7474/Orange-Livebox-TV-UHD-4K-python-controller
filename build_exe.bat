@echo off
echo ============================================================
echo Compilation de Livebox TV Controller en un seul fichier .exe
echo ============================================================
echo.

REM Verifier si PyInstaller est installe
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installation de PyInstaller...
    pip install pyinstaller
)

echo Creation de l'executable autonome...
pyinstaller --noconsole --onefile --name "LiveboxTVController" --icon "app_icon.ico" --add-data "keys.json;." --add-data "epg_ids.json;." tvOrangeGui.py

echo.
if exist "dist\LiveboxTVController.exe" (
    echo ============================================================
    echo SUCCES ! Votre executable est pret :
    echo dist\LiveboxTVController.exe
    echo ============================================================
) else (
    echo Une erreur est survenue lors de la generation du binaire.
)

pause
