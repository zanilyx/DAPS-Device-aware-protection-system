@echo off
title Update Network Monitor Structure

echo ===========================================
echo Updating Network Monitor Structure...
echo ===========================================
echo.

:: Make sure we're inside the project
if not exist "network_monitor" (
    echo ERROR: network_monitor folder not found.
    pause
    exit /b
)

cd network_monitor

:: -------------------------------
:: Root Files
:: -------------------------------

if not exist "main.py" type nul > main.py
if not exist "requirements.txt" type nul > requirements.txt
if not exist "README.md" type nul > README.md
if not exist "settings.json" type nul > settings.json

if not exist "whitelist.txt" (
(
echo # Trusted IPs
echo 8.8.8.8
echo 1.1.1.1
) > whitelist.txt
)

if not exist "blacklist.txt" (
(
echo # Suspicious IPs
echo 45.45.45.45
echo 10.10.10.10
) > blacklist.txt
)

:: -------------------------------
:: Core
:: -------------------------------

if not exist "core" mkdir core

for %%f in (
capture.py
parser.py
flows.py
session.py
interface.py
) do (
    if not exist "core\%%f" type nul > "core\%%f"
)

:: -------------------------------
:: UI
:: -------------------------------

if not exist "ui" mkdir ui

if not exist "ui\dashboard.py" type nul > ui\dashboard.py

:: -------------------------------
:: Utils
:: -------------------------------

if not exist "utils" mkdir utils

for %%f in (
config.py
ip_utils.py
) do (
    if not exist "utils\%%f" type nul > "utils\%%f"
)

:: -------------------------------
:: Database
:: -------------------------------

if not exist "database" mkdir database

if not exist "database\database.py" type nul > database\database.py

:: -------------------------------
:: Models
:: -------------------------------

if not exist "models" mkdir models

for %%f in (
packet.py
flow.py
session.py
) do (
    if not exist "models\%%f" type nul > "models\%%f"
)

:: -------------------------------
:: Output folders
:: -------------------------------

if not exist "exports" mkdir exports
if not exist "logs" mkdir logs

echo.
echo Creating default settings.json...

(
echo {
echo     "refresh_rate": 1,
echo     "capture_filter": "",
echo     "resolve_hostnames": false,
echo     "track_ipv6": true,
echo     "ignore_loopback": true,
echo     "upload_alert_mb": 50,
echo     "dashboard_sort": "upload"
echo }
) > settings.json

echo.
echo ===========================================
echo Structure Updated Successfully!
echo ===========================================
echo.

tree /F

pause