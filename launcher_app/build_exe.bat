@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist venv (
  py -3.12 -m venv venv || py -3 -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller
if not exist mods mkdir mods
set ADD=--add-data "assets;assets"
dir /b mods\beevisual-*.jar >nul 2>nul && set ADD=%ADD% --add-data "mods;mods"
pyinstaller --noconsole --onefile --name BeeVisual --icon assets\logo\icon.ico %ADD% main.py
echo.
echo Готово: dist\BeeVisual.exe  (клиент BeeVisual уже внутри, если был собран build.bat клиента)
pause
