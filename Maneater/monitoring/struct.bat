o off
title Network Monitor Project Generator

echo ==========================================
echo      Creating Network Monitor Project
echo ==========================================

:: Root Folder
mkdir network_monitor

:: Move into project
cd network_monitor

:: Python Files
type nul > main.py
type nul > capture.py
type nul > parser.py
type nul > statistics.py
type nul > dashboard.py
type nul > config.py
type nul > ip_utils.py
type nul > logger.py

:: Config Files
type nul > whitelist.txt
type nul > blacklist.txt

:: Documentation
type nul > README.md
type nul > requirements.txt

:: Create logs folder
mkdir logs

:: Default whitelist
(
echo # Whitelisted IP Addresses
echo 8.8.8.8
echo 1.1.1.1
) > whitelist.txt

:: Default blacklist
(
echo # Blacklisted IP Addresses
echo 10.10.10.10
) > blacklist.txt

:: Default requirements
(
echo scapy
echo rich
echo psutil
echo colorama
echo netifaces
) > requirements.txt

echo.
echo ==========================================
echo Project created successfully!
echo ==========================================
echo.

tree /F

pause
