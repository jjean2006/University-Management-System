# Student University Management System (UMS)

A complete, high-performance web frontend and Flask backend for a comprehensive university database management system, built as a **Database Systems (DBMS) Project** adhering to the specifications of **DBMS Project Review 1** and **DBMS Project Review 2**.

---

## Project Overview

This project implements an end-to-end institutional database management system using:
- **MySQL 8.0**: Relational database engine enforcing strict relational integrity, composite foreign key constraints across Levels 0 through 4, and 6 specialized analytical SQL views.
- **Flask (Python 3.12)**: Lightweight, modular backend micro-framework implementing role-based access control (RBAC), parameterized SQL execution (SQL injection immune), and server-side session authentication.
- **Basic Web Development**: Clean, semantic **HTML5**, **Vanilla CSS3**, and **Vanilla JavaScript** (ES6+) with zero npm/Node.js build dependencies, no bloated front-end frameworks, and a strictly neutral, clutter-free institutional interface.

---

## Complete Login Credentials

All institutional members in the university database (administrative staff, all faculty members, and all students) have active accounts configured. You can sign in using either their **Username / ID** or their official **Email Address**.

### 1. Core Administrative & Staff Accounts

| Role | Username / ID | Password | Email Address | Access & Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | `admin@vit.ac.in` | Academic administration, department budgets, course creation, user account provisioning |
| **Accounts / Bursar** | `accounts` | `accounts123` | `accounts@vit.ac.in` | Financial dashboard, issue student dues, record fee payments, fee defaulters directory |
| **Hostel Warden** | `warden` | `warden123` | `warden@vit.ac.in` | Hostel blocks, floor plans, room capacities, occupied/vacant bed audit, resident directory |
| **Faculty Demo** | `faculty` | `faculty123` | `ramesh.kumar@vit.ac.in` | Assigned course rosters, lecture attendance marking, shortage warnings (< 75%) |
| **Student Demo** | `student` | `student123` | `jacob.jean2025@vitstudent.ac.in` | Academic profile, course enrollment, waitlists, hostel room details, fee ledger |

### 2. All Faculty Logins in Database

All faculty members can log in using their **Employee Code** (or email) with default password **`password`**:

| Employee Code | Faculty Full Name | Academic Designation | Department | Official Email | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `EMP1001` | Dr. Ramesh Kumar | Professor | Computer Science & Engineering | `ramesh.kumar@vit.ac.in` | `password` |
| `EMP1002` | Dr. Priya Sundaram | Associate Professor | Computer Science & Engineering | `priya.sundaram@vit.ac.in` | `password` |
| `EMP1003` | Prof. Anand Venkatesh | Assistant Professor | Electronics & Communication | `anand.venkatesh@vit.ac.in` | `password` |

### 3. All Student Logins in Database

All enrolled students can log in using their **Registration Number** (or email) with default password **`password`**:

| Registration No | Student Full Name | Degree Programme | Department | Official Student Email | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `25BAI0077` | Jacob Jean | B.Tech CSE (AI & ML) | Computer Science & Engg | `jacob.jean2025@vitstudent.ac.in` | `password` |
| `25BCE0634` | Aradhya Jain | B.Tech CSE (Core) | Computer Science & Engg | `aradhya.jain2025@vitstudent.ac.in` | `password` |
| `25BAI0030` | Krrish Pare | B.Tech CSE (AI & ML) | Computer Science & Engg | `krrish.pare2025@vitstudent.ac.in` | `password` |
| `25ECE0122` | Nikhil Sharma | B.Tech ECE | Electronics & Communication | `nikhil.sharma2025@vitstudent.ac.in` | `password` |
| `25BCE0899` | Sneha Rao | B.Tech CSE (Core) | Computer Science & Engg | `sneha.rao2025@vitstudent.ac.in` | `password` |

> [!NOTE]
> **Dynamic User Provisioning**: The Administrator dashboard (`/admin/dashboard`) features an **"Add Institutional User & Entity Account"** interface. Adding a student or faculty member inserts all relational attributes into `STUDENT` or `FACULTY` and immediately creates a synchronized login in `USER_ACCOUNT`.

---

## How to Run the Project

### Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed.
- **MySQL Server**: MySQL 8.0 (or MariaDB 10.5+) running locally.
- **Git** (optional, for cloning).

---

### A. Running on Linux

#### Option 1: Automated Single-Script Launch
```bash
# Clone the repository (if not already inside project directory)
git clone git@github.com:jjean2006/University-Management-System.git
cd University-Management-System

# Run the unified startup script (starts user-space MySQL daemon, configures venv, starts Flask)
chmod +x start.sh run_mysql.sh
./start.sh
```

#### Option 2: Manual Linux Setup
```bash
# 1. Start the user-space MySQL instance (or use system service: sudo systemctl start mysql)
./run_mysql.sh

# 2. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Initialize and seed database if starting fresh
python3 schema/init_db.py

# 5. Launch the Flask development server
python3 run.py
```
Open your browser and navigate to: **http://localhost:5000**

---

### B. Running on macOS

#### 1. Install & Start MySQL (via Homebrew)
```bash
# Install MySQL if not already installed
brew install mysql

# Start the MySQL background service
brew services start mysql
```

#### 2. Create MySQL User & Database
Open MySQL terminal:
```bash
mysql -u root
```
Run the following SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS university_db;
CREATE USER IF NOT EXISTS 'jacob'@'localhost' IDENTIFIED BY 'password';
CREATE USER IF NOT EXISTS 'jacob'@'127.0.0.1' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON university_db.* TO 'jacob'@'localhost';
GRANT ALL PRIVILEGES ON university_db.* TO 'jacob'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. Set Up Python & Launch App
```bash
# Clone repository and enter directory
cd University-Management-System

# Create virtual environment and activate
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Seed the database schema, views, and data
python3 schema/init_db.py

# Run the Flask server
python3 run.py
```
Open your browser and navigate to: **http://localhost:5000**

---

### C. Running on Windows

#### 1. Install MySQL Server
Install **MySQL Server 8.0** via [MySQL Community Installer](https://dev.mysql.com/downloads/installer/) or using **XAMPP**.
Ensure the MySQL service is running on port `3306`. You can use your existing `root` account (no extra MySQL user is needed).

#### 2. Configure Your Database Credentials
Copy the template and put **your own** MySQL username and password in it:
```powershell
copy .env.example .env
notepad .env
```
`.env` is git-ignored, so every team member keeps their own credentials locally.

#### 3. Set Up Virtual Environment & Run (PowerShell / Command Prompt)
```powershell
# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1          # (Command Prompt: venv\Scripts\activate.bat)

# Install dependencies
pip install -r requirements.txt

# Create university_db, its tables, views and sample data
python schema\init_db.py

# Launch the Flask application
python run.py
```
Open your browser and navigate to: **http://localhost:5000**

---

### Database Connection Configuration

Connection settings are read from a **`.env`** file in the project root (copy `.env.example`). Variables already set in the shell override the file.

| Variable | Example | Description |
| :--- | :--- | :--- |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | `your_mysql_password` | MySQL password |
| `DB_HOST` | `127.0.0.1` | MySQL host address |
| `DB_PORT` | `3306` | MySQL TCP port (the app also tries `3307`) |
| `DB_NAME` | `university_db` | Database name |

`schema/init_db.py` and the app both use these settings on Windows, macOS and Linux.

### Running the Test Suite
```bash
python -m pytest tests -q
```
The suite (300+ tests) runs against the database in `.env`; `tests/test_tier5_crud_validation.py` re-seeds the sample data before and after it runs.

---

## Relational Database Architecture

### 13 Normalized Relational Tables
1. **`DEPARTMENT`**: Academic departments with annual operating budgets.
2. **`SEMESTER`**: Academic terms, start/end dates, and registration windows.
3. **`HOSTEL_BLOCK`**: Campus residential buildings with gender segregation.
4. **`PROGRAMME`**: Degree programmes (B.Tech CSE, AIML, ECE) mapped to departments.
5. **`FACULTY`**: Academic faculty members, official designations, and department affiliations.
6. **`COURSE`**: Course catalog with credits, capacities, available seats, and recursive prerequisites.
7. **`HOSTEL_ROOM`**: Physical rooms within blocks, room capacity, and monthly rent.
8. **`STUDENT`**: Student records with CGPA, programme, advisor, and room allocations.
9. **`ENROLLMENT`**: Course registrations with grade points and completion statuses.
10. **`ATTENDANCE`**: Daily lecture attendance tracking (Present/Absent).
11. **`COURSE_WAITLIST`**: Priority-queued overflow waitlists for capacity-constrained courses.
12. **`FEE_PAYMENT`**: Tuition billing invoices, dues, paid amounts, and payment statuses.
13. **`USER_ACCOUNT`**: Centralized authentication, hashed passwords, roles, and entity linking.

### 6 Analytical Database Views
- `v_admin_student_directory`: Aggregated student performance, programme, advisor, and residential details.
- `v_faculty_attendance_shortage`: Automated tracking of students with attendance below 75% threshold.
- `v_accounts_fee_summary`: Aggregation of billed, collected, and outstanding tuition revenue.
- `v_accounts_defaulters_list`: Detailed directory of students with unsettled fee balances.
- `v_warden_occupancy_overview`: Real-time block-level bed capacities, occupied beds, and vacancies.
- `v_warden_resident_directory`: Floor-by-floor listing of resident boarders and room allocations.

---

## Input Validation & Data Integrity

All forms are validated on the server before any SQL runs, and multi-step changes run inside a single MySQL transaction:
- Registration numbers, employee codes, course codes, invoice numbers, emails and phone numbers must match their formats.
- CGPA must be 0.00–10.00; credits 1–6; capacity 1–300; amounts cannot be negative.
- Payments cannot exceed the outstanding balance; partially paid overdue invoices stay `OVERDUE`.
- Hostel allocation checks the block's gender and the room's free beds, and updates `occupied_beds`.
- Attendance can only be recorded for students enrolled in the course and not for future dates.
- Enrolling locks the course row (`SELECT ... FOR UPDATE`) so the last seat cannot be taken twice.
- New user accounts never overwrite an existing username.

---

## Role-Based Features

### 1. Academic Administrator (`/admin/dashboard`)
- University overview: academic departments and annual budgetary allocations.
- Degree programmes catalog and faculty/student directories.
- Real-time course enrollment capacity and waitlist monitor.
- **Add New Course Offering**: Interactive form to create new courses with code, title, credits, capacity, department, and prerequisites.
- **Add Institutional User & Entity Account**: Provision users for any role (`student`, `faculty`, `admin`, `accounts`, `warden`) with automatic entity table synchronization.
- **System User Accounts Directory**: Live audit table showing all active login accounts, assigned roles, and linked entity IDs.
- **Server-side Search**: SQL `LIKE` search across students (reg no, name, email, programme, department, advisor) and courses.
- **Manage Course Offerings**: Edit a course's title, credits and capacity, or delete a course that has no enrolled students.
- **Delete Student**: Removes the student and their login; cascades to enrollments, attendance, waitlists and fees, and releases their course seats and hostel bed.

### 2. Faculty Portal (`/faculty/dashboard`)
- View assigned lecture sections, student counts, and course capacities.
- Real-time attendance shortage alerts (< 75% threshold) with debarment warnings.
- **Mark Daily Lecture Attendance**:
  - Individual student attendance selection (course, student, date, and status).
  - Batch class attendance sheet with quick toggle actions.

### 3. Student Academic Portal (`/student/dashboard`)
- **First Section**: Student Academic Profile & Hostel Allocation.
- **Second Section**: Registered Courses & Semester Grade History.
- **Third Section**: Course Registration & Available Offerings:
  - Browse course catalog with seat availability and prerequisites.
  - Sign up / enroll directly if seats are available (`seats > 0`).
  - Join waitlist with priority queue position tracking if the course is full.
  - **Drop** an in-progress course, which releases the seat.
- **Fourth Section**: Tuition Fee Invoices & Payment Ledger.

### 4. Financial Accounts & Bursar (`/accounts/dashboard`)
- **1. Issue New Student Fee Invoice & Dues**: Create new student invoices with due dates and payment amounts.
- **2. Record Fee Payment Update**: Transactional payment recorder; payments cannot exceed the outstanding balance.
- **Cancel Invoice**: Delete an invoice that has not received any payment.
- **3. Fee Defaulters Directory**: Audit directory of students with outstanding balances.
- **4. Complete Invoicing Ledger**: Comprehensive fee ledger with real-time filtering by payment status and student ID.
- **Revenue Summary KPIs**: Overview of billed, collected, and outstanding balances.

### 5. Hostel Warden Portal (`/warden/dashboard`)
- Overview of hostel blocks (capacities, gender segregation).
- Room occupancy breakdown (occupied beds, vacant bed counts, monthly rent).
- Resident student directory with room and programme mapping.

---

## Project Structure

```
.
├── app/
│   ├── auth.py                  # Role definitions, session guards & authentication
│   ├── config.py                # Database configuration & environment fallbacks
│   ├── db.py                    # Database connection, query execution & transaction helper
│   ├── validators.py            # Server-side form validation helpers
│   ├── __init__.py              # Flask application factory (create_app)
│   ├── routes/
│   │   ├── accounts_routes.py   # Accounts dashboard, invoicing & payment routes
│   │   ├── admin_routes.py      # Admin dashboard, course creation & user provisioning
│   │   ├── auth_routes.py       # Login portal, credential validation & logout
│   │   ├── common.py            # Shared styling & view constants
│   │   ├── faculty_routes.py    # Faculty roster & lecture attendance routes
│   │   ├── student_routes.py    # Student profile, enrollment & waitlist routes
│   │   └── warden_routes.py     # Hostel rooms & resident directory routes
│   ├── static/
│   │   ├── css/
│   │   │   ├── base.css         # Typography, neutral theme variables & reset
│   │   │   ├── components.css   # Tables, matte badges, buttons, forms, modals & toasts
│   │   │   ├── dashboard.css    # Role dashboard cards, KPIs & grids
│   │   │   └── layout.css       # Navigation header & layout container
│   │   └── js/
│   │       ├── attendance.js    # Interactive attendance calculation & batch toggle
│   │       ├── main.js          # Toast notifications & UI helpers
│   │       ├── payments.js      # Fee payment modal & ledger status/student filters
│   │       └── table-filter.js  # Instant search & sorting on all data tables
│   └── templates/
│       ├── base.html            # Main base shell template
│       ├── accounts/            # Accounts dashboard templates
│       ├── admin/               # Admin dashboard templates
│       ├── auth/                # Institutional login portal template
│       ├── errors/              # 403, 404, 500 error pages
│       ├── faculty/             # Faculty dashboard & attendance marking
│       ├── student/             # Student profile, catalog & waitlist
│       └── warden/              # Warden block & room occupancy templates
├── schema/
│   ├── init_db.py               # Complete database setup & verification runner
│   ├── schema.sql               # 13 relational DDL tables (Topological order)
│   ├── seed_data.sql            # Sample DML dataset and user accounts
│   └── views.sql                # 6 analytical SQL views
├── .env.example                 # Template for each member's local MySQL credentials
├── credentials.txt              # Plaintext demo credentials reference sheet
├── requirements.txt             # Python package dependencies
├── run_mysql.sh                 # User-space MySQL launcher & initializer
├── run.py                       # Flask application entry point
├── start.sh                     # Unified Linux startup script
└── README.md                    # Project documentation
```
