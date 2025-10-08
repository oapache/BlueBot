@echo off
title Starting Telegram and WhatsApp Bot...

echo Starting Telegram bot (Python)...
start cmd /k "cd /d %~dp0 && python bot.py"

echo Starting WhatsApp bot (TypeScript)...
start cmd /k "cd /d %~dp0\Whatsapp && npx ts-node server.ts"

echo Everything is ready! Press any key to close this window :D
pause >nul