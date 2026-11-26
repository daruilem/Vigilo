@echo off
rem Double-click to start Vigilo with the verified active scan. Open Docker Desktop first.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1" -Active
