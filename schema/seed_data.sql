-- University Management System (UMS)
-- Sample Seed Data (Section 4 DML from Review 2 Specification)

-- 1. DEPARTMENT (3 rows)
INSERT INTO DEPARTMENT (dept_code, dept_name, building, budget) VALUES
('SCOPE', 'School of Computer Science and Engineering', 'Technology Tower', 15000000.00),
('SENSE', 'School of Electronics Engineering', 'M. Visvesvaraya Block', 12000000.00),
('SMEC', 'School of Mechanical Engineering', 'GD Naidu Block', 10000000.00);

-- 2. PROGRAMME (3 rows)
INSERT INTO PROGRAMME (programme_code, programme_name, degree_level, total_credits_required, dept_id) VALUES
('BTECH-CSE-AIML', 'B.Tech in Computer Science and Engineering (AI & ML)', 'Undergraduate', 160, 1),
('BTECH-CSE-CORE', 'B.Tech in Computer Science and Engineering', 'Undergraduate', 160, 1),
('BTECH-ECE', 'B.Tech in Electronics and Communication Engineering', 'Undergraduate', 160, 2);

-- 3. FACULTY (3 rows)
INSERT INTO FACULTY (employee_code, first_name, last_name, email, phone, designation, dept_id) VALUES
('EMP1001', 'Ramesh', 'Kumar', 'ramesh.kumar@vit.ac.in', '9876543210', 'Professor', 1),
('EMP1002', 'Priya', 'Sundaram', 'priya.sundaram@vit.ac.in', '9876543211', 'Associate Professor', 1),
('EMP1003', 'Anand', 'Venkatesh', 'anand.venkatesh@vit.ac.in', '9876543212', 'Assistant Professor', 2);

-- 4. SEMESTER (2 rows)
INSERT INTO SEMESTER (academic_year, term, start_date, end_date, is_active) VALUES
('2026-2027', 'Fall', '2026-07-15', '2026-11-30', 1),
('2026-2027', 'Winter', '2026-12-15', '2027-04-30', 0);

-- 5. COURSE (4 rows)
INSERT INTO COURSE (course_code, course_title, credits, capacity, available_seats, dept_id, prereq_course_id) VALUES
('CSE1001', 'Problem Solving and Object-Oriented Programming', 4, 60, 0, 1, NULL),
('CSE2001', 'Data Structures and Algorithms', 4, 60, 0, 1, 1),
('CSE2005', 'Database Management Systems', 4, 60, 2, 1, 2),
('ECE1002', 'Semiconductor Devices and Circuits', 3, 60, 15, 2, NULL);

-- 6. HOSTEL_BLOCK (2 rows)
INSERT INTO HOSTEL_BLOCK (block_name, gender_type, total_capacity) VALUES
('Men Block A', 'M', 500),
('Ladies Block B', 'F', 400);

-- 7. HOSTEL_ROOM (3 rows)
INSERT INTO HOSTEL_ROOM (block_id, room_number, floor_number, capacity, occupied_beds, monthly_rent) VALUES
(1, 'A-201', 2, 2, 2, 8500.00),
(1, 'A-202', 2, 2, 1, 8500.00),
(2, 'B-105', 1, 2, 1, 9500.00);

-- 8. STUDENT (5 rows)
INSERT INTO STUDENT (reg_no, first_name, last_name, email, dob, gender, cgpa, programme_id, advisor_id, room_id) VALUES
('25BAI0077', 'Jacob', 'Jean', 'jacob.jean2025@vitstudent.ac.in', '2005-04-12', 'M', 9.45, 1, 1, 1),
('25BCE0634', 'Aradhya', 'Jain', 'aradhya.jain2025@vitstudent.ac.in', '2005-08-22', 'F', 9.12, 2, 2, 3),
('25BAI0030', 'Krrish', 'Pare', 'krrish.pare2025@vitstudent.ac.in', '2005-01-18', 'M', 8.85, 1, 1, 1),
('25ECE0122', 'Nikhil', 'Sharma', 'nikhil.sharma2025@vitstudent.ac.in', '2004-11-05', 'M', 7.90, 3, 3, 2),
('25BCE0899', 'Sneha', 'Rao', 'sneha.rao2025@vitstudent.ac.in', '2005-03-30', 'F', 8.20, 2, 2, NULL);

-- 9. ENROLLMENT (7 rows)
INSERT INTO ENROLLMENT (student_id, course_id, semester_id, enrollment_date, grade_points, completion_status) VALUES
(1, 1, 1, '2026-07-20', 10.00, 'COMPLETED'),
(1, 2, 1, '2026-07-20', 9.50, 'COMPLETED'),
(1, 3, 1, '2026-07-21', NULL, 'ENROLLED'),
(2, 1, 1, '2026-07-20', 9.00, 'COMPLETED'),
(2, 3, 1, '2026-07-21', NULL, 'ENROLLED'),
(3, 3, 1, '2026-07-21', NULL, 'ENROLLED'),
(4, 4, 1, '2026-07-22', NULL, 'ENROLLED');

-- 10. ATTENDANCE (9 rows)
INSERT INTO ATTENDANCE (student_id, course_id, attendance_date, status) VALUES
(1, 3, '2026-08-01', 'Present'),
(1, 3, '2026-08-03', 'Present'),
(1, 3, '2026-08-05', 'Present'),
(2, 3, '2026-08-01', 'Present'),
(2, 3, '2026-08-03', 'Absent'),
(2, 3, '2026-08-05', 'Present'),
(3, 3, '2026-08-01', 'Absent'),
(3, 3, '2026-08-03', 'Absent'),
(3, 3, '2026-08-05', 'Present');

-- 11. COURSE_WAITLIST (2 rows)
INSERT INTO COURSE_WAITLIST (student_id, course_id, waitlist_time, priority_position, status) VALUES
(4, 2, '2026-07-21 09:30:15.120', 1, 'ACTIVE'),
(5, 2, '2026-07-21 09:45:22.450', 2, 'ACTIVE');

-- 12. FEE_PAYMENT (4 rows)
INSERT INTO FEE_PAYMENT (student_id, invoice_no, total_amount, paid_amount, due_date, payment_status, payment_date) VALUES
(1, 'INV-2026-001', 195000.00, 195000.00, '2026-08-10', 'PAID', '2026-08-02'),
(2, 'INV-2026-002', 205000.00, 205000.00, '2026-08-10', 'PAID', '2026-08-05'),
(3, 'INV-2026-003', 195000.00, 100000.00, '2026-08-10', 'PARTIAL', '2026-08-08'),
(4, 'INV-2026-004', 185000.00, 0.00, '2026-08-10', 'OVERDUE', NULL);
