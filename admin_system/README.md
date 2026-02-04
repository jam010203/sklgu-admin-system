# SKLGU Admin System

A comprehensive admin dashboard system for Sangguniang Kabataan Local Government Unit.

## Features

- ✅ Admin-only account creation
- ✅ User password management with admin visibility
- ✅ Secure authentication (@sklgu.gov.ph email validation)
- ✅ File upload and database storage
- ✅ Budget automation and tracking
- ✅ Inventory record management
- ✅ Fillable and printable forms

## Project Structure

```
admin_system/
├── app.py                  # Main Flask application
├── database/              # SQLite database files
├── static/
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── templates/            # HTML templates
│   └── admin-login.html # Admin login page
├── uploads/             # Uploaded files storage
└── requirements.txt     # Python dependencies
```

## Installation

1. Install dependencies:
```bash
cd admin_system
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the admin portal:
```
http://localhost:5000
```

## Default Admin Credentials

- Email: admin@sklgu.gov.ph
- Password: admin123 (Please change immediately!)

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Email domain validation
- Password change tracking
- Admin visibility of user passwords (for recovery purposes)

© 2026 SKLGU. All rights reserved.
