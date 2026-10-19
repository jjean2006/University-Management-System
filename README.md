# Student University Management System (UMS)

A modular, clean, and high-performance web frontend and Flask backend for a comprehensive university management database, built according to the specifications in **DBMS Project Review 1** and **DBMS Project Review 2**.

---

## Architecture & Technology Stack

- **Backend**: Python 3.12, Flask 3.1, `mysql-connector-python`
- **Database**: MySQL 8.0 (`university_db`), user `jacob` / password `password`
- **Relational Schema**: 12 normalized relational tables (Level 0 through Level 4 foreign key dependencies)
- **Analytical Views**: 6 analytical database views (`v_admin_student_directory`, `v_faculty_attendance_shortage`, `v_accounts_fee_summary`, `v_accounts_defaulters_list`, `v_warden_occupancy_overview`, `v_warden_resident_directory`)
- **Frontend**: Server-rendered Jinja2 templates, semantic HTML5, modular Vanilla CSS & JS (zero npm build step required)
- **Design Philosophy**: Strictly neutral, institutional typography, high data density, subtle 150ms transitions, and strict adherence to the Anti-AI design checklist (no flashy neons, no purple gradients, no heavy drop shadows, no glassmorphism).

---

## Role-Based Features

### 1. Academic Administrator
- Overview of academic departments and annual budgetary allocations.
- Degree programmes catalog and faculty/student directories.
- Real-time course enrollment capacity and waitlist monitor.
- **Add New Course Offering**: Interactive form to create new courses with code, title, credits, capacity, department, and prerequisites.

### 2. Faculty
- View assigned lecture sections and course capacities.
- Real-time attendance shortage alerts (< 75% threshold) with debarment warnings.
- **Mark Daily Lecture Attendance**:
  - Individual student attendance selection (course, student, date, and Present/Absent status).
  - Batch class attendance sheet with "Select All Present" / "Select All Absent" quick actions.

### 3. Student
- View personal academic profile, CGPA, degree programme, and department.
- Residential hostel room allocation and block details.
- Registered courses and semester grade history.
- **Course Registration & Sign-Up**:
  - Browse available course catalog with department, credits, prerequisites, and seat availability.
  - Sign up / enroll directly if seats are available (`seats > 0`) with automatic prerequisite validation.
  - Join waitlist with priority queue position tracking if the course is full (`seats == 0`).
- Tuition fee invoice ledger with balance due and payment status.

### 4. Accounts & Finance (Bursar)
- Revenue aggregation KPIs (total billed, collected revenue, outstanding balance).
- Defaulter audit directory for tracking overdue tuition balances.
- **Issue Fee Invoice & Dues**: Create new student invoices with due dates and payment amounts.
- **Record Fee Payments**: Transactional payment recorder updating invoice status (`PAID`, `PARTIAL`, `PENDING`).

### 5. Hostel Warden
- Overview of hostel blocks (capacities, gender segregation).
- Room occupancy breakdown (occupied beds, vacant bed counts, monthly rent).
- Resident student directory with room and programme mapping.

---

## Demo Credentials

All test credentials and access scopes are documented in [`credentials.txt`](credentials.txt):

| Role | Username | Password | Alternate ID | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | — | University-wide administration & course catalog |
| **Faculty** | `faculty` | `faculty123` | `EMP1001` / `password` | Course rosters & lecture attendance marking |
| **Student** | `student` | `student123` | `25BAI0077` / `password` | Profile, course sign-up, waitlists & fee ledger |
| **Accounts** | `accounts` | `accounts123` | — | Revenue metrics, issuing dues & recording payments |
| **Hostel Warden** | `warden` | `warden123` | — | Hostel blocks, vacant beds & resident directory |

---

## Quick Start Guide

### 1. Single Command Startup
```bash
./start.sh
```
This script automatically:
1. Starts the user-space MySQL daemon on `/tmp/mysql.sock` (port `3307`).
2. Configures the Python virtual environment (`venv`).
3. Launches the Flask server on **http://localhost:5000**.

### 2. Manual Startup
```bash
# 1. Start the MySQL database daemon
./run_mysql.sh

# 2. Activate virtualenv and run server
source venv/bin/activate
python run.py
```

### 3. Access the Web Portal
Open your browser and navigate to:
```
http://localhost:5000
```

---

## Project Structure

```
.
├── app/
│   ├── auth.py                  # Role definitions, session guards & credentials
│   ├── config.py                # Database and session configuration
│   ├── db.py                    # Multi-driver database abstraction layer
│   ├── __init__.py              # Flask application factory (create_app)
│   ├── routes/
│   │   ├── accounts_routes.py   # Accounts dashboard & payment routes
│   │   ├── admin_routes.py      # Admin dashboard & course creation routes
│   │   ├── auth_routes.py       # Login & session authentication
│   │   ├── common.py            # Shared styling & view constants
│   │   ├── faculty_routes.py    # Faculty roster & attendance routes
│   │   ├── student_routes.py    # Student profile, enrollment & waitlist routes
│   │   └── warden_routes.py     # Hostel rooms & resident directory routes
│   ├── static/
│   │   ├── css/
│   │   │   ├── base.css         # Typography, neutral theme & reset
│   │   │   ├── components.css   # Tables, matte badges, buttons, forms, modals
│   │   │   ├── dashboard.css    # Role dashboard cards, KPIs & layouts
│   │   │   └── layout.css       # Navigation header & layout container
│   │   └── js/
│   │       ├── attendance.js    # Interactive attendance calculation & batch toggle
│   │       ├── main.js          # Flash message dismissals & UI helpers
│   │       ├── payments.js      # Fee payment modal & ledger updates
│   │       └── table-filter.js  # Instant search & filtering on all data tables
│   └── templates/
│       ├── base.html            # Main base template
│       ├── accounts/            # Accounts dashboard templates
│       ├── admin/               # Admin dashboard templates
│       ├── auth/                # Institutional login portal template
│       ├── errors/              # 403, 404, 500 error pages
│       ├── faculty/             # Faculty dashboard & attendance marking
│       ├── student/             # Student profile, catalog & waitlist
│       └── warden/              # Warden block & room occupancy templates
├── schema/
│   ├── init_db.py               # Database setup & seeding runner
│   ├── schema.sql               # 12 relational DDL tables
│   ├── seed_data.sql            # Review 2 sample DML dataset
│   └── views.sql                # 6 analytical SQL views
├── credentials.txt              # Demo credentials reference sheet
├── requirements.txt             # Python package dependencies
├── run_mysql.sh                 # User-space MySQL launcher & initializer
├── run.py                       # Flask application entry point
├── start.sh                     # Unified startup script
└── README.md                    # Project documentation
```
