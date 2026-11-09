# BeeVisual client (Fabric, Minecraft 1.21.4)

## Что нужно (бесплатно)
1. JDK 21 (Temurin): https://adoptium.net
2. Gradle 8.12 (https://gradle.org/install) ИЛИ IntelliJ IDEA Community (откроешь папку и запустишь задачу `build`).

## Сборка
Положи папку `BeeVisual_client` рядом с `launcher_app` и запусти `build.bat`.
Готовый `beevisual-1.0.0.jar` сам скопируется в `launcher_app\mods`. Лаунчер подхватит его при запуске.

## Управление в игре
- Правый Shift - меню модулей (ЛКМ вкл/выкл, ПКМ настройки, колесо - прокрутка)
- C - зум (модуль Zoom)
- Настройки сохраняются в `.beevisual\minecraft\config\beevisual.json`

## Модули
HUD: Watermark, FeatureList, Speedometer, SessionInfo, TargetHUD, InventoryPreview, Cooldowns, Keystrokes, Coords, PotionHUD, ArmorHUD
Рендер: Trails, JumpCircles, ChinaHat, FullBright, Zoom
Мир: WeatherControl, Ambience, SnowGround (снег)

## Если сборка не прошла
Пришли весь красный текст из окна сборки (там указаны файл и строка).
