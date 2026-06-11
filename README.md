# Secure File Protection, Monitoring & DLP System

## Overview

This project is a Python-based Data Loss Prevention (DLP), File Encryption, Access Control, and Monitoring platform.

The system is designed to:

- Encrypt files using AES-256
- Classify files (Internal, Confidential, Restricted)
- Control which devices can access files
- Monitor file activity
- Detect USB devices
- Log all security events
- Generate audit reports
- Detect suspicious behavior and possible data exfiltration

---

## Objectives

1. Protect sensitive files using strong encryption.
2. Restrict file access to authorized users and devices.
3. Monitor file activity in real time.
4. Track USB usage and removable media activity.
5. Maintain detailed audit trails.
6. Detect unauthorized access attempts.
7. Provide reporting and security analytics.

---

## Major Features

### File Intake System

- Detect newly added files
- Generate unique file IDs
- Calculate SHA-256 hashes
- Register files in database

### AES-256 Encryption

- Encrypt confidential files
- AES-256-GCM encryption
- Secure key generation
- Envelope encryption architecture

### File Classification

Supported classifications:

- Public
- Internal
- Confidential
- Restricted

Classification methods:

- Manual classification
- Rule-based classification
- AI-assisted classification (future enhancement)

### Access Control

- User authentication
- Device authentication
- Permission-based access
- Read/Write/Delete controls

### Device Registration

Store:

- Device ID
- Hostname
- MAC Address
- Operating System
- User Information

### Secure Decryption

Before decrypting:

1. Verify user identity
2. Verify device authorization
3. Verify access permissions
4. Log activity

### File Monitoring

Monitor:

- Open
- Read
- Modify
- Rename
- Move
- Copy
- Delete

### USB Monitoring

Detect:

- USB insertion
- USB removal
- USB file transfers
- Unauthorized USB devices

### USB Security Controls

- USB whitelisting
- Device fingerprinting
- Copy detection
- Data exfiltration detection

### Audit Logging

Log:

- User actions
- Device actions
- File actions
- Authentication events
- USB events
- Alert events

### Alert Engine

Generate alerts for:

- Unauthorized access
- Unknown USB devices
- Excessive file copying
- Large data transfers
- Multiple failed logins
- Suspicious activity

### Reporting

Generate:

- Security reports
- User activity reports
- USB activity reports
- Audit reports

---

## Project Architecture

File Intake
→ Encryption Engine
→ Classification Engine
→ Access Control
→ Monitoring Services
→ USB Detection
→ Audit Logging
→ Alert Engine
→ Dashboard & Reports

---

## Proposed Folder Structure

```text
project/
│
├── controller.py
├── config.py
│
├── database/
│   ├── db.py
│   ├── models.py
│
├── encryption/
│   ├── encrypt.py
│   └── decrypt.py
│
├── classification/
│   └── classifier.py
│
├── monitoring/
│   ├── file_monitor.py
│   ├── usb_monitor.py
│   └── integrity_monitor.py
│
├── access_control/
│   ├── users.py
│   ├── devices.py
│   └── permissions.py
│
├── logging_system/
│   ├── audit_logger.py
│   └── alerts.py
│
├── reports/
│   └── report_generator.py
│
└── dashboard/
    └── gui.py
```

---

## Database Tables

### Users

- User information
- Authentication data

### Devices

- Registered devices
- Device metadata

### Files

- File details
- Classification
- Encryption status

### Permissions

- File access mappings

### Audit Logs

- Security activity records

### USB Logs

- USB monitoring events

### Alerts

- Triggered security alerts

---

## Technologies

### Backend

- Python

### Encryption

- cryptography
- AES-256-GCM

### Monitoring

- watchdog
- psutil

### Authentication

- bcrypt
- pyotp

### Database

- SQLite

### Dashboard

- PyQt6 (planned)

### Reporting

- pandas
- reportlab

---

## Future Enhancements

- AI-based file classification
- Machine learning anomaly detection
- Cloud synchronization
- Centralized management server
- Role-Based Access Control (RBAC)
- Endpoint agent architecture
- Enterprise policy engine
- Email/SMS alerting
- Web dashboard

---

## Educational Value

This project combines concepts from:

- Cybersecurity
- Cryptography
- Digital Rights Management (DRM)
- Data Loss Prevention (DLP)
- Endpoint Security
- Digital Forensics
- Access Control Systems
- Secure Software Development

---

## Status

Design and architecture phase.
Modules will be developed incrementally.
