-- University Management System (UMS)
-- Analytical and Operational Views DDL (6 Core Analytical Views + 2 Supplemental Views)

DROP VIEW IF EXISTS v_warden_resident_directory;
DROP VIEW IF EXISTS v_warden_occupancy_overview;
DROP VIEW IF EXISTS v_accounts_defaulters_list;
DROP VIEW IF EXISTS v_accounts_fee_summary;
DROP VIEW IF EXISTS v_faculty_attendance_shortage;
DROP VIEW IF EXISTS v_faculty_view;
DROP VIEW IF EXISTS v_admin_course_waitlist;
DROP VIEW IF EXISTS v_admin_student_directory;

-- 1. Administrator Student Directory View
CREATE VIEW v_admin_student_directory AS
SELECT
  s.student_id,
  s.reg_no,
  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
  s.email,
  p.programme_name,
  d.dept_name,
  CONCAT(f.first_name, ' ', f.last_name) AS faculty_advisor,
  s.cgpa
FROM STUDENT s
JOIN PROGRAMME p ON s.programme_id = p.programme_id
JOIN DEPARTMENT d ON p.dept_id = d.dept_id
LEFT JOIN FACULTY f ON s.advisor_id = f.faculty_id;

-- 2. Faculty Attendance Shortage Alert View (< 75.00%)
CREATE VIEW v_faculty_attendance_shortage AS
SELECT
  c.course_code,
  c.course_title,
  s.reg_no,
  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
  s.email AS student_email,
  COUNT(a.attendance_date) AS total_classes_conducted,
  SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS classes_attended,
  ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_date)) * 100, 2) AS attendance_percentage
FROM ATTENDANCE a
JOIN COURSE c ON a.course_id = c.course_id
JOIN STUDENT s ON a.student_id = s.student_id
GROUP BY c.course_id, c.course_code, c.course_title, s.student_id, s.reg_no, s.first_name, s.last_name
HAVING attendance_percentage < 75.00;

-- 3. Accounts Fee Revenue Summary View
CREATE VIEW v_accounts_fee_summary AS
SELECT
  f.payment_status,
  COUNT(f.payment_id) AS total_invoices,
  SUM(f.total_amount) AS total_billed_amount,
  SUM(f.paid_amount) AS total_collected_amount,
  SUM(f.total_amount - f.paid_amount) AS outstanding_balance
FROM FEE_PAYMENT f
GROUP BY f.payment_status;

-- 4. Accounts Fee Defaulters List View (PENDING, PARTIAL, OVERDUE)
CREATE VIEW v_accounts_defaulters_list AS
SELECT
  s.reg_no,
  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
  s.email,
  f.invoice_no,
  f.total_amount,
  f.paid_amount,
  (f.total_amount - f.paid_amount) AS balance_due,
  f.due_date,
  f.payment_status
FROM FEE_PAYMENT f
JOIN STUDENT s ON f.student_id = s.student_id
WHERE f.payment_status IN ('PENDING', 'PARTIAL', 'OVERDUE');

-- 5. Warden Room Occupancy Overview View
CREATE VIEW v_warden_occupancy_overview AS
SELECT
  hb.block_name,
  hb.gender_type,
  hr.room_number,
  hr.floor_number,
  hr.capacity,
  hr.occupied_beds,
  (hr.capacity - hr.occupied_beds) AS vacant_beds,
  hr.monthly_rent
FROM HOSTEL_ROOM hr
JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id
ORDER BY hb.block_name, hr.room_number;

-- 6. Warden Resident Directory View
CREATE VIEW v_warden_resident_directory AS
SELECT
  hb.block_name,
  hr.room_number,
  s.reg_no,
  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
  s.gender,
  s.email,
  p.programme_name
FROM STUDENT s
JOIN HOSTEL_ROOM hr ON s.room_id = hr.room_id
JOIN HOSTEL_BLOCK hb ON hr.block_id = hb.block_id
JOIN PROGRAMME p ON s.programme_id = p.programme_id
ORDER BY hb.block_name, hr.room_number, s.reg_no;

-- Supplemental View 1: Admin Course Waitlist Overview
CREATE VIEW v_admin_course_waitlist AS
SELECT
  c.course_id,
  c.course_code,
  c.course_title,
  d.dept_code,
  c.capacity,
  c.available_seats,
  (c.capacity - c.available_seats) AS enrolled_students,
  COUNT(w.waitlist_id) AS total_waitlisted
FROM COURSE c
JOIN DEPARTMENT d ON c.dept_id = d.dept_id
LEFT JOIN COURSE_WAITLIST w ON c.course_id = w.course_id AND w.status = 'ACTIVE'
GROUP BY c.course_id, c.course_code, c.course_title, d.dept_code, c.capacity, c.available_seats;

-- Supplemental View 2: Faculty Active Course Roster View
CREATE VIEW v_faculty_view AS
SELECT
  c.course_code,
  c.course_title,
  s.reg_no,
  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
  s.email AS student_email,
  e.enrollment_date,
  e.completion_status
FROM ENROLLMENT e
JOIN COURSE c ON e.course_id = c.course_id
JOIN STUDENT s ON e.student_id = s.student_id
WHERE e.completion_status = 'ENROLLED';
