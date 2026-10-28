@echo off
cd /d "%~dp0"
python arayuz.py
if errorlevel 1 pause
