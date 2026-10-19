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
Ensure MySQL service is running on default port `3306`.

Open **MySQL Command Line Client** or **PowerShell** and create the user/database:
```sql
CREATE DATABASE IF NOT EXISTS university_db;
CREATE USER IF NOT EXISTS 'jacob'@'localhost' IDENTIFIED BY 'password';
CREATE USER IF NOT EXISTS 'jacob'@'127.0.0.1' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON university_db.* TO 'jacob'@'localhost';
GRANT ALL PRIVILEGES ON university_db.* TO 'jacob'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;
```
*(If your MySQL root user already has a different password, see Environment Configuration below).*

#### 2. Set Up Virtual Environment & Run (PowerShell / Command Prompt)
Open PowerShell or Command Prompt in the project directory:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# In PowerShell:
.\venv\Scripts\Activate.ps1
# (Or in Command Prompt: venv\Scripts\activate.bat)

# Install dependencies
pip install -r requirements.txt

# Initialize database schema, analytical views, and seed data
python schema\init_db.py

# Launch the Flask application
python run.py
```
Open your browser and navigate to: **http://localhost:5000**

---

### Database Connection Configuration (Optional)

The application automatically connects using sensible defaults (`jacob` / `password` on port `3307` or `3306`). If your MySQL configuration differs, customize via environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DB_USER` | `jacob` (or `root`) | MySQL username |
| `DB_PASSWORD` | `password` | MySQL password |
| `DB_HOST` | `127.0.0.1` | MySQL host address |
| `DB_PORT` | `3307` (fallbacks to `3306`) | MySQL TCP port |
| `DB_NAME` | `university_db` | Database catalog name |

**Example (Windows PowerShell):**
```powershell
$env:DB_USER="root"
$env:DB_PASSWORD="your_mysql_password"
$env:DB_PORT="3306"
python run.py
```

**Example (Linux / macOS):**
```bash
export DB_USER="root"
export DB_PASSWORD="your_mysql_password"
export DB_PORT="3306"
python run.py
```

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

## Role-Based Features

### 1. Academic Administrator (`/admin/dashboard`)
- University overview: academic departments and annual budgetary allocations.
- Degree programmes catalog and faculty/student directories.
- Real-time course enrollment capacity and waitlist monitor.
- **Add New Course Offering**: Interactive form to create new courses with code, title, credits, capacity, department, and prerequisites.
- **Add Institutional User & Entity Account**: Provision users for any role (`student`, `faculty`, `admin`, `accounts`, `warden`) with automatic entity table synchronization.
- **System User Accounts Directory**: Live audit table showing all active login accounts, assigned roles, and linked entity IDs.

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
- **Fourth Section**: Tuition Fee Invoices & Payment Ledger.

### 4. Financial Accounts & Bursar (`/accounts/dashboard`)
- **1. Issue New Student Fee Invoice & Dues**: Create new student invoices with due dates and payment amounts.
- **2. Record Fee Payment Update**: Transactional payment recorder with instant toast notifications.
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
│   ├── db.py                    # Database connection pool & query execution abstraction
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
├── credentials.txt              # Plaintext demo credentials reference sheet
├── requirements.txt             # Python package dependencies
├── run_mysql.sh                 # User-space MySQL launcher & initializer
├── run.py                       # Flask application entry point
├── start.sh                     # Unified Linux startup script
└── README.md                    # Project documentation
```
