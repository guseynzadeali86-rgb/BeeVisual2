@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === 1/2 Собираю клиент (мод) ===
call BeeVisual_client\build.bat
echo === 2/2 Собираю BeeVisual.exe ===
call launcher_app\build_exe.bat
echo.
echo ИТОГ: launcher_app\dist\BeeVisual.exe
pause
