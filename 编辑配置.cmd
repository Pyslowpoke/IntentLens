@echo off
cd /d "%~dp0"
if not exist ".env" copy /y ".env.example" ".env" >nul
notepad.exe ".env"
