# DAPS – Device Aware Protection System

## Overview

DAPS (Device Aware Protection System) is a modular endpoint security and Data Loss Prevention (DLP) platform designed to protect sensitive organizational data through encryption, device-aware access control, activity monitoring, and security auditing.

The platform combines file protection, device trust verification, user authentication, monitoring services, and forensic logging into a unified security architecture.

DAPS aims to reduce the risk of unauthorized data access, accidental data leakage, malicious insider activity, and unauthorized device usage while maintaining complete audit visibility.

---

## Core Objectives

* Protect sensitive organizational files using strong encryption.
* Restrict access based on authorized users and trusted devices.
* Monitor file, system, and device activity in real time.
* Detect suspicious behavior and potential data exfiltration attempts.
* Maintain comprehensive audit trails for compliance and investigations.
* Provide centralized visibility into security-related events.

---

## System Modules

### Filecrypter

The Filecrypter module serves as the primary data protection layer.

#### Features

* AES-256-GCM file encryption
* Secure file decryption
* File integrity verification
* SHA-256 hash generation
* Secure key management
* Encryption policy enforcement

#### Purpose

Ensures that sensitive files remain protected even if copied, stolen, or accessed outside authorized environments.

---

### Maneater

Maneater is the monitoring and detection engine responsible for observing system activity.

#### Features

* File activity monitoring
* Process monitoring
* Network activity inspection
* File transfer detection
* Security event generation
* Suspicious behavior detection

#### Monitored Events

* File creation
* File modification
* File deletion
* File movement
* Process execution
* Large file transfers
* Abnormal activity patterns

#### Purpose

Provides visibility into endpoint activity and enables early detection of potential security incidents.

---

### Sandbox

The Sandbox module provides an isolated environment for controlled file execution and analysis.

#### Features

* Suspicious file analysis
* Isolated execution environment
* Behavioral observation
* Security assessment reports
* Threat investigation support

#### Purpose

Allows potentially unsafe files to be examined without affecting the host system.

---

### User Base

The User Base module manages identities, devices, and authorization policies.

#### Features

* User management
* Authentication services
* Device registration
* Trusted device management
* Permission enforcement
* Role-based access control (future)

#### Device Information

Stored device information may include:

* Device identifier
* Hostname
* MAC address
* Operating system information
* Registration status

#### Purpose

Ensures that protected resources are only accessible to authorized users operating from trusted devices.

---

### Logging System

The Logging System provides security auditing and forensic visibility.

#### Features

* Security event logging
* User activity logging
* Device activity logging
* Authentication tracking
* Alert recording
* Investigation support

#### Logged Events

* Login attempts
* File access
* Encryption actions
* Decryption actions
* Device registration
* USB activity
* Security alerts

#### Purpose

Creates a complete audit trail for compliance, troubleshooting, and forensic analysis.

---

## Security Features

### Device-Aware Access Control

DAPS evaluates both:

* User identity
* Device trust status

before granting access to protected resources.

### USB Monitoring

DAPS can monitor removable media activity including:

* USB insertion
* USB removal
* File copy operations
* Unknown device detection

### Alert Engine

Security alerts may be generated for:

* Unauthorized access attempts
* Unknown devices
* Excessive file copying
* Large data transfers
* Repeated authentication failures
* Suspicious user behavior

---

## Project Architecture

```text
User
 │
 ▼
Authentication
 │
 ▼
Device Verification
 │
 ▼
Access Control
 │
 ▼
Filecrypter
 │
 ▼
Protected Files
 │
 ├─────────────► Logging System
 │
 ├─────────────► Maneater
 │
 └─────────────► Sandbox
```

---

## Repository Structure

```text
DAPS/
│
├── Main/
│   ├── main.py
│   ├── dashboard.py
│   └── config.py
│
├── Filecrypter/
│
├── Maneater/
│
├── Sandbox/
│
├── User_base/
│
├── Logs/
│
├── README.md
│
└── requirements.txt
```

---

## Technology Stack

### Programming Language

* Python

### Cryptography

* cryptography
* AES-256-GCM
* SHA-256

### Monitoring

* watchdog
* psutil
* pywin32

### Authentication

* bcrypt
* pyotp

### Database

* SQLite

### Reporting

* pandas
* reportlab

### User Interface

* Tkinter
* PyQt6 (future)

---

## Future Roadmap

### Phase 1

* Core encryption engine
* Logging framework
* User management
* Device registration

### Phase 2

* File monitoring
* USB monitoring
* Alert generation
* Reporting system

### Phase 3

* Advanced threat detection
* Behavioral analytics
* Enterprise policy management
* Centralized administration

### Phase 4

* AI-assisted classification
* Anomaly detection
* Multi-endpoint deployment
* Cloud integration

---

## Educational Focus

DAPS combines concepts from:

* Cybersecurity
* Cryptography
* Data Loss Prevention (DLP)
* Endpoint Security
* Digital Forensics
* Secure Software Development
* Access Control Systems
* Threat Detection

---

## Project Status

Current Status: Active Development

DAPS is being developed incrementally using a modular architecture, allowing each subsystem to be designed, tested, and integrated independently.
