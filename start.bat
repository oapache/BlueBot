@echo off
title Starting Telegram and WhatsApp Bot...
setlocal

if exist ".venv312\Scripts\activate.bat" (
  call ".venv312\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

echo Starting Telegram bot (Python)...
start cmd /k "cd /d %~dp0 && python bot.py"

echo Starting WhatsApp bot (TypeScript)...
start cmd /k "cd /d %~dp0 && npx ts-node Whatsapp\server.ts"

echo Everything is ready! Press any key to close this window :D
pause >nul
