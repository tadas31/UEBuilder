@echo off

SET PlatformsConfig=./PlatformsConfig.json
SET ProjectConfig=./ProjectConfig.json

call py main.py --platformsConfig=%PlatformsConfig% --projectConfig=%ProjectConfig%

pause
