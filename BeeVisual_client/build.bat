@echo off
chcp 65001 >nul
cd /d "%~dp0"
where java >nul 2>nul
if errorlevel 1 goto nojava
if exist gradlew.bat goto build
where gradle >nul 2>nul
if errorlevel 1 goto nogradle
call gradle wrapper --gradle-version 8.12
:build
call gradlew.bat build
if errorlevel 1 goto fail
if not exist "..\launcher_app\mods" mkdir "..\launcher_app\mods"
for %%f in (build\libs\beevisual-*.jar) do copy /Y "%%f" "..\launcher_app\mods\" >nul
echo.
echo ГОТОВО: jar лежит в build\libs и скопирован в ..\launcher_app\mods
pause
exit /b 0
:nojava
echo Нужен JDK 21: https://adoptium.net (Temurin 21), потом открой новое окно и запусти снова
pause
exit /b 1
:nogradle
echo Нужен Gradle 8.12: https://gradle.org/install  ИЛИ открой эту папку в IntelliJ IDEA Community и запусти задачу build
pause
exit /b 1
:fail
echo.
echo ОШИБКА СБОРКИ - пришли мне текст ошибки выше
pause
exit /b 1
