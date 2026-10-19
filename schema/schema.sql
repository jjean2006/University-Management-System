-- University Management System (UMS)
-- Relational Database Schema DDL (12 Tables in Topological Order)
-- Engine: MySQL 8.0+ InnoDB, Charset: utf8mb4

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS FEE_PAYMENT;
DROP TABLE IF EXISTS COURSE_WAITLIST;
DROP TABLE IF EXISTS ATTENDANCE;
DROP TABLE IF EXISTS ENROLLMENT;
DROP TABLE IF EXISTS STUDENT;
DROP TABLE IF EXISTS HOSTEL_ROOM;
DROP TABLE IF EXISTS COURSE;
DROP TABLE IF EXISTS FACULTY;
DROP TABLE IF EXISTS PROGRAMME;
DROP TABLE IF EXISTS HOSTEL_BLOCK;
DROP TABLE IF EXISTS SEMESTER;
DROP TABLE IF EXISTS DEPARTMENT;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. DEPARTMENT
CREATE TABLE DEPARTMENT (
    dept_id INT AUTO_INCREMENT,
    dept_code VARCHAR(10) NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    building VARCHAR(50) NOT NULL,
    budget DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT pk_department PRIMARY KEY (dept_id),
    CONSTRAINT uk_dept_code UNIQUE (dept_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. SEMESTER
CREATE TABLE SEMESTER (
    semester_id INT AUTO_INCREMENT,
    academic_year VARCHAR(10) NOT NULL,
    term VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT pk_semester PRIMARY KEY (semester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. HOSTEL_BLOCK
CREATE TABLE HOSTEL_BLOCK (
    block_id INT AUTO_INCREMENT,
    block_name VARCHAR(50) NOT NULL,
    gender_type CHAR(1) NOT NULL,
    total_capacity INT NOT NULL,
    CONSTRAINT pk_hostel_block PRIMARY KEY (block_id),
    CONSTRAINT uk_block_name UNIQUE (block_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. PROGRAMME
CREATE TABLE PROGRAMME (
    programme_id INT AUTO_INCREMENT,
    programme_code VARCHAR(15) NOT NULL,
    programme_name VARCHAR(100) NOT NULL,
    degree_level VARCHAR(20) NOT NULL,
    total_credits_required INT NOT NULL,
    dept_id INT NOT NULL,
    CONSTRAINT pk_programme PRIMARY KEY (programme_id),
    CONSTRAINT uk_programme_code UNIQUE (programme_code),
    CONSTRAINT fk_programme_dept FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. FACULTY
CREATE TABLE FACULTY (
    faculty_id INT AUTO_INCREMENT,
    employee_code VARCHAR(15) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    designation VARCHAR(50) NOT NULL,
    dept_id INT NOT NULL,
    CONSTRAINT pk_faculty PRIMARY KEY (faculty_id),
    CONSTRAINT uk_faculty_emp_code UNIQUE (employee_code),
    CONSTRAINT uk_faculty_email UNIQUE (email),
    CONSTRAINT fk_faculty_dept FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. COURSE
CREATE TABLE COURSE (
    course_id INT AUTO_INCREMENT,
    course_code VARCHAR(15) NOT NULL,
    course_title VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    capacity INT NOT NULL,
    available_seats INT NOT NULL,
    dept_id INT NOT NULL,
    prereq_course_id INT NULL,
    CONSTRAINT pk_course PRIMARY KEY (course_id),
    CONSTRAINT uk_course_code UNIQUE (course_code),
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id) ON DELETE RESTRICT,
    CONSTRAINT fk_course_prereq FOREIGN KEY (prereq_course_id)
        REFERENCES COURSE(course_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. HOSTEL_ROOM
CREATE TABLE HOSTEL_ROOM (
    room_id INT AUTO_INCREMENT,
    block_id INT NOT NULL,
    room_number VARCHAR(10) NOT NULL,
    floor_number INT NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    occupied_beds INT NOT NULL DEFAULT 0,
    monthly_rent DECIMAL(8,2) NOT NULL,
    CONSTRAINT pk_hostel_room PRIMARY KEY (room_id),
    CONSTRAINT uk_block_room UNIQUE (block_id, room_number),
    CONSTRAINT fk_room_block FOREIGN KEY (block_id)
        REFERENCES HOSTEL_BLOCK(block_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. STUDENT
CREATE TABLE STUDENT (
    student_id INT AUTO_INCREMENT,
    reg_no VARCHAR(15) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    gender CHAR(1) NOT NULL,
    cgpa DECIMAL(3,2) NOT NULL DEFAULT 0.00,
    programme_id INT NOT NULL,
    advisor_id INT NULL,
    room_id INT NULL,
    CONSTRAINT pk_student PRIMARY KEY (student_id),
    CONSTRAINT uk_student_reg_no UNIQUE (reg_no),
    CONSTRAINT uk_student_email UNIQUE (email),
    CONSTRAINT fk_student_programme FOREIGN KEY (programme_id)
        REFERENCES PROGRAMME(programme_id) ON DELETE RESTRICT,
    CONSTRAINT fk_student_advisor FOREIGN KEY (advisor_id)
        REFERENCES FACULTY(faculty_id) ON DELETE SET NULL,
    CONSTRAINT fk_student_room FOREIGN KEY (room_id)
        REFERENCES HOSTEL_ROOM(room_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. ENROLLMENT
CREATE TABLE ENROLLMENT (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    grade_points DECIMAL(4,2) NULL,
    completion_status VARCHAR(20) NOT NULL DEFAULT 'ENROLLED',
    CONSTRAINT pk_enrollment PRIMARY KEY (student_id, course_id),
    CONSTRAINT fk_enrollment_student FOREIGN KEY (student_id)
        REFERENCES STUDENT(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_enrollment_course FOREIGN KEY (course_id)
        REFERENCES COURSE(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_enrollment_semester FOREIGN KEY (semester_id)
        REFERENCES SEMESTER(semester_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. ATTENDANCE
CREATE TABLE ATTENDANCE (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL,
    CONSTRAINT pk_attendance PRIMARY KEY (student_id, course_id, attendance_date),
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id)
        REFERENCES STUDENT(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_course FOREIGN KEY (course_id)
        REFERENCES COURSE(course_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. COURSE_WAITLIST
CREATE TABLE COURSE_WAITLIST (
    waitlist_id INT AUTO_INCREMENT,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    waitlist_time TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    priority_position INT NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT pk_course_waitlist PRIMARY KEY (waitlist_id),
    CONSTRAINT uk_student_course_waitlist UNIQUE (student_id, course_id),
    CONSTRAINT fk_waitlist_student FOREIGN KEY (student_id)
        REFERENCES STUDENT(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_waitlist_course FOREIGN KEY (course_id)
        REFERENCES COURSE(course_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. FEE_PAYMENT
CREATE TABLE FEE_PAYMENT (
    payment_id INT AUTO_INCREMENT,
    student_id INT NOT NULL,
    invoice_no VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    due_date DATE NOT NULL,
    payment_status VARCHAR(15) NOT NULL DEFAULT 'PENDING',
    payment_date DATE NULL,
    CONSTRAINT pk_fee_payment PRIMARY KEY (payment_id),
    CONSTRAINT uk_invoice_no UNIQUE (invoice_no),
    CONSTRAINT fk_fee_student FOREIGN KEY (student_id)
        REFERENCES STUDENT(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. USER_ACCOUNT (Authentication & System Access)
CREATE TABLE IF NOT EXISTS USER_ACCOUNT (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    entity_id INT NULL,
    display_name VARCHAR(100) NULL,
    email VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

