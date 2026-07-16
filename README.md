# DAPS - Device-Aware Protection System

A comprehensive enterprise-grade device protection and data security system with USB monitoring, file encryption, role-based access control, and audit logging.

## 🎯 Overview

DAPS is an integrated solution designed to protect sensitive organizational data by:
- **Monitoring and controlling USB devices** in real-time
- **Encrypting sensitive files** with AES-256 encryption using astronomical data as entropy sources
- **Managing user roles and permissions** with department-level access controls
- **Maintaining comprehensive audit logs** for compliance and security investigations
- **Providing a modern, intuitive GUI** for system administration and user interactions

## ✨ Key Features

### 🔐 File Encryption
- **AES-256 Encryption**: Military-grade file encryption with 256-bit keys
- **Unique Key Generation**: Uses ISS position, planetary coordinates, and timestamps to generate cryptographically unique encryption keys
- **Secure Key Storage**: Encrypted keys stored in SQLite database with access tracking
- **File-Level Permissions**: Role-based access control for encrypted files

### 🔌 USB Device Management
- **Real-time Monitoring**: Detects and monitors all connected USB storage devices
- **Device Authentication**: SHA256-based device identification and authorization
- **Whitelist Management**: Register and authorize USB devices per user
- **Automatic Blocking**: Prevents unauthorized USB devices from being accessed
- **Comprehensive Logging**: Tracks all USB device events and attempts

### 👥 User & Access Management
- **Role-Based Access Control (RBAC)**: Admin, Manager, and User roles
- **Department-Level Restrictions**: IT, HR, Finance with department-specific permissions
- **User Database**: Stores user credentials, roles, departments, and metadata
- **Device Registration**: Links users to their approved devices
- **Permission Hierarchy**: Department ceilings + role permissions for fine-grained control

### 📊 Audit & Compliance
- **Comprehensive Audit Logging**: Records all file access, modifications, and deletions
- **USB Activity Tracking**: Logs all USB device connections and events
- **User Activity Monitoring**: Tracks login attempts, file operations, and device access
- **Compliance Reports**: Generate audit trails for regulatory compliance (SOX, HIPAA, GDPR)
- **Timestamp Verification**: All events include precise timestamps and device information

### 🎨 User Interface
- **Modern GUI**: Built with PySide6 for a sleek, modern interface
- **Dark Theme**: Eye-friendly dark color scheme optimized for professional environments
- **Responsive Design**: Adaptive layouts for different screen sizes
- **User Dashboard**: Quick access to encrypted files, device status, and recent activity
- **Profile Management**: User profile popup with role and department information

## 📦 Project Structure

```
DAPS-Device-aware-protection-system/
├── Main/
│   └── Universal_GUI.py          # Main application entry point and GUI shell
├── GUI_modules/
│   ├── Login_page_GUI.py          # Authentication interface
│   ├── Home_GUI.py                # Dashboard and main content area
│   └── progress_dialog.py          # Progress tracking UI component
├── Filecrypter/
│   ├── encryption/
│   │   ├── key.py                # AES-256 key generation with astronomical data
│   │   ├── encrypt.py            # File encryption operations
│   │   └── decrypt.py            # File decryption operations
│   └── gui/                       # Encryption GUI components
├── Maneater/
│   └── monitoring/
│       └── usb_monitor/
│           ├── usb_auth.py       # USB device authentication and authorization
│           ├── usb_info.py       # USB device detection and enumeration
│           ├── usb_log.py        # USB event logging
│           └── usb_control.py    # USB device control (block/allow)
├── User_base/
│   ├── permissions/
│   │   ├── permissions.py        # RBAC and permission management
│   │   ├── roles.py              # Role definitions
│   │   └── department.py         # Department definitions
│   └── authentication/
│       └── auth.py               # User authentication and session management
├── database/
│   ├── users.py                 # User database schema and operations
│   ├── devices.py               # Device database schema and operations
│   ├── files.py                 # File metadata database operations
│   ├── logs.py                  # Audit logging database operations
│   ├── keys.py                  # Encryption key storage operations
│   └── users.db                 # SQLite user database
└── README.md
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Windows 10+ (for USB device monitoring features)
- Administrator privileges (for USB control features)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/zanilyx/DAPS-Device-aware-protection-system.git
   cd DAPS-Device-aware-protection-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\\Scripts\\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize databases**
   ```bash
   # Create user database
   python database/users.py
   
   # Create device database
   python database/devices.py
   
   # Create file database
   python database/files.py
   
   # Create audit logs
   python database/logs.py
   
   # Create encryption keys database
   python database/keys.py
   ```

5. **Run the application**
   ```bash
   python Main/Universal_GUI.py
   ```

## 🚀 Usage

### User Authentication
1. Launch the application
2. Enter username and password
3. Authentication validates credentials against the user database
4. Successful authentication loads your personalized dashboard

### Managing Encrypted Files
- **Encrypt Files**: Select files to encrypt → assign permissions → system generates unique AES-256 key
- **Decrypt Files**: Choose encrypted file → verify authentication → system retrieves and applies encryption key
- **Set Permissions**: Define which roles can read, write, or delete files

### USB Device Management
- **Register Device**: Connect USB → application detects → admin registers with user
- **Monitor Status**: View all connected USB devices and their authorization status
- **Block Unauthorized**: System automatically prevents access to unregistered USB devices

### Audit & Monitoring
- **View Audit Logs**: Access comprehensive logs of all file and device operations
- **Export Reports**: Generate compliance reports for regulatory requirements
- **Monitor Activity**: Real-time view of user activity and security events

## 🔐 Security Architecture

### Encryption
- **Algorithm**: AES-256 (Advanced Encryption Standard, 256-bit key)
- **Key Generation**: Combines:
  - ISS (International Space Station) real-time position coordinates
  - Mercury planetary ephemeris data
  - Pluto planetary ephemeris data
  - UTC timestamp
  - SHA256 hash of the combined material
- **Key Storage**: Encrypted keys stored in dedicated SQLite database with access logging

### Access Control
```
Permission Model:
Department Ceiling (Max permissions per department)
        ↓
Role Permissions (What role can do)
        ↓
Final Access Level (intersection of both)
```

**Departments & Permissions:**
- IT: READ, WRITE, DELETE
- HR: READ, WRITE
- FINANCE: READ

**Roles & Permissions:**
- ADMIN: READ, WRITE, DELETE
- MANAGER: READ, WRITE
- USER: READ

### Device Authentication
- SHA256 hashing of device manufacturer, model, and PNP device ID
- Hardware-based device identification
- Whitelist/blacklist management
- Real-time device monitoring

## 📋 API Reference

### Key Classes

#### `USBAuthenticator`
```python
auth = USBAuthenticator()
results = auth.authenticate_all()  # Verify all connected USB devices
status, owner = auth.authenticate_device(device)  # Verify single device
```

#### `Permission` System
```python
from User_base.permissions.permissions import check_access
allowed = check_access(user_dept, user_role, requested_permission)
```

#### File Encryption
```python
from Filecrypter.encryption.key import build_metadata, generate_key
metadata = build_metadata()  # Gather astronomical data
key = generate_key(metadata)  # Generate AES-256 key
```

#### Audit Logging
```python
from database.logs import log_event
log_event(username, file_id, action, details)
```

## 📊 Database Schema

### users table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    department TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### usb_devices table
```sql
CREATE TABLE usb_devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE NOT NULL,
    manufacturer TEXT NOT NULL,
    device_name TEXT NOT NULL,
    model TEXT NOT NULL,
    pnp_device_id TEXT NOT NULL,
    owner TEXT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### audit_logs table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username TEXT,
    device_id TEXT,
    file_id TEXT,
    action TEXT,
    details TEXT
)
```

### usb_logs table
```sql
CREATE TABLE usb_logs (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username TEXT,
    USB_Type TEXT
)
```

### keys table
```sql
CREATE TABLE keys (
    id INTEGER PRIMARY KEY,
    file_id TEXT UNIQUE,
    aes_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
)
```

## 🎨 UI/UX Features

- **Color Scheme**:
  - Deep Background: `#0D1B2A`
  - Surface: `#1C2E42`
  - Primary Accent (Ice Blue): `#4A9EBF`
  - Primary Text: `#F0F4F8`
  - Secondary Text: `#8FA8BF`

- **Components**:
  - Avatar with glowing accent ring
  - Profile popup with user information
  - Responsive header with app branding
  - Stacked page navigation
  - Progress dialogs for long operations
  - Custom styled buttons and inputs

## 🧪 Testing

Each module includes testing capabilities:

```bash
# Test USB authentication
python Maneater/monitoring/usb_monitor/usb_auth.py

# Test database operations
python database/testing_db.py

# Test encryption key generation
python Filecrypter/encryption/key.py

# Test permission system
python User_base/permissions/permissions.py
```

## 📝 Logging

The system maintains three primary log types:

1. **Audit Logs** (`audit_logs` table): File access, modifications, deletions
2. **USB Logs** (`usb_logs` table): USB device connections and authorizations
3. **Application Logs** (console): Runtime events and errors

Access logs via:
```python
import sqlite3
conn = sqlite3.connect("database/logs.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
for row in cursor.fetchall():
    print(row)
```

## 🔒 Compliance & Security Considerations

- **SOX Compliance**: Comprehensive audit trails for financial data
- **HIPAA Ready**: Protected health information access logging
- **GDPR Support**: User data management and audit capabilities
- **Device Control**: Prevent unauthorized data exfiltration via USB
- **Encryption**: Military-grade AES-256 for sensitive files
- **Authentication**: Credentials stored with password hashing
- **Audit Trail**: Immutable logs of all operations for investigation

## 🚧 Future Enhancements

- [ ] Multi-factor authentication (MFA)
- [ ] Cloud-based audit log storage
- [ ] Machine learning-based anomaly detection
- [ ] Integration with Active Directory/LDAP
- [ ] Mobile app for remote monitoring
- [ ] Hardware security module (HSM) support
- [ ] Advanced encryption with key escrow
- [ ] Biometric authentication support

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Security Notice

This system handles sensitive organizational data. Please:
- Use strong, unique passwords for all accounts
- Regularly update and patch all dependencies
- Keep encryption keys secure and backed up
- Perform regular security audits
- Monitor audit logs for suspicious activity
- Run on secure, isolated networks when possible

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact the development team
- Check existing documentation and FAQs

## 👨‍💻 Development Team

- **Original Developer**: zanilyx
- **Repository**: https://github.com/zanilyx/DAPS-Device-aware-protection-system

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Active Development