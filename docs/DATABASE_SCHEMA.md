# Database Schema Reference

> **Generated from the SQLAlchemy models** (`app/models/`) — do not edit by hand. Regenerate with `python tools/generate_docs.py` after any model change.

**32 tables.** Every tenant-owned table carries an indexed `school_id` foreign key — see [ARCHITECTURE.md](ARCHITECTURE.md) for how multi-tenancy is enforced.

## Foundation (Phase 0)

### `schools`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `name` | VARCHAR(150) | no |  |
| `slug` | VARCHAR(80) | no | indexed; unique |
| `logo_path` | VARCHAR(255) | yes |  |
| `address` | VARCHAR(255) | yes |  |
| `phone` | VARCHAR(30) | yes |  |
| `email` | VARCHAR(120) | yes |  |
| `website` | VARCHAR(150) | yes |  |
| `registration_number` | VARCHAR(80) | yes |  |
| `is_active` | BOOLEAN | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

### `users`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | yes | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(120) | no |  |
| `email` | VARCHAR(150) | no | indexed; unique |
| `password_hash` | VARCHAR(255) | no |  |
| `role` | user_role | no | indexed |
| `phone` | VARCHAR(30) | yes |  |
| `is_verified` | BOOLEAN | no |  |
| `verification_token` | VARCHAR(255) | yes | unique |
| `verification_token_expires_at` | TIMESTAMP WITH TIME ZONE | yes |  |
| `is_active_account` | BOOLEAN | no |  |
| `last_login_at` | TIMESTAMP WITH TIME ZONE | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `` on (verification_token)
- **CHECK** `ck_super_admin_has_no_school`: `(role = 'SUPER_ADMIN' AND school_id IS NULL) OR (role != 'SUPER_ADMIN' AND school_id IS NOT NULL)`

### `academic_sessions`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(50) | no |  |
| `start_date` | DATE | no |  |
| `end_date` | DATE | no |  |
| `is_active` | BOOLEAN | no |  |
| `description` | TEXT | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_session_school_name` on (school_id, name)
- **CHECK** `ck_session_end_after_start`: `end_date > start_date`
- **UNIQUE INDEX** `uq_one_active_session_per_school` on (school_id) — partial

### `classes`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(80) | no |  |
| `code` | VARCHAR(30) | yes |  |
| `class_teacher_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `capacity` | INTEGER | yes |  |
| `status` | class_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_class_school_session_name` on (school_id, session_id, name)

### `sections`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(30) | no |  |
| `room` | VARCHAR(30) | yes |  |
| `class_teacher_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `capacity` | INTEGER | yes |  |
| `status` | section_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_section_class_name` on (class_id, name)

### `subjects`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `teacher_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `name` | VARCHAR(100) | no |  |
| `code` | VARCHAR(30) | no |  |
| `max_marks` | INTEGER | no |  |
| `passing_marks` | INTEGER | no |  |
| `subject_type` | subject_type | no |  |
| `status` | subject_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_subject_school_class_code` on (school_id, class_id, code)
- **CHECK** `ck_subject_passing_le_max`: `passing_marks <= max_marks`

### `school_settings`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); unique |
| `grading_system` | JSON | no |  |
| `passing_percentage` | FLOAT | no |  |
| `attendance_late_threshold_minutes` | INTEGER | no |  |
| `minimum_attendance_percentage` | FLOAT | no |  |
| `fee_fine_per_day` | NUMERIC(10, 2) | no |  |
| `default_payment_methods` | JSON | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `` on (school_id)

### `audit_logs`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | yes | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `user_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL); indexed |
| `action` | VARCHAR(80) | no | indexed |
| `table_name` | VARCHAR(80) | no |  |
| `record_id` | INTEGER | yes |  |
| `old_value` | JSON | yes |  |
| `new_value` | JSON | yes |  |
| `ip_address` | VARCHAR(45) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no | indexed |

## People (Phase 1)

### `guardians`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `father_name` | VARCHAR(120) | yes |  |
| `mother_name` | VARCHAR(120) | yes |  |
| `phone` | VARCHAR(30) | no |  |
| `alternate_phone` | VARCHAR(30) | yes |  |
| `email` | VARCHAR(150) | yes |  |
| `occupation` | VARCHAR(120) | yes |  |
| `address` | VARCHAR(255) | yes |  |
| `emergency_contact_name` | VARCHAR(120) | yes |  |
| `emergency_contact_phone` | VARCHAR(30) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

### `students`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `admission_number` | VARCHAR(40) | no | indexed |
| `name` | VARCHAR(150) | no |  |
| `father_name` | VARCHAR(120) | yes |  |
| `mother_name` | VARCHAR(120) | yes |  |
| `date_of_birth` | DATE | yes |  |
| `gender` | student_gender | yes |  |
| `cnic_or_bform` | VARCHAR(40) | yes |  |
| `blood_group` | VARCHAR(5) | yes |  |
| `phone` | VARCHAR(30) | yes |  |
| `email` | VARCHAR(150) | yes |  |
| `address` | VARCHAR(255) | yes |  |
| `city` | VARCHAR(100) | yes |  |
| `previous_school` | VARCHAR(150) | yes |  |
| `admission_date` | DATE | no |  |
| `photo_path` | VARCHAR(255) | yes |  |
| `medical_info` | TEXT | yes |  |
| `notes` | TEXT | yes |  |
| `status` | student_status | no | indexed |
| `current_session_id` | INTEGER | yes | FK → `academic_sessions.id` (ON DELETE SET NULL) |
| `current_class_id` | INTEGER | yes | FK → `classes.id` (ON DELETE SET NULL) |
| `current_section_id` | INTEGER | yes | FK → `sections.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_student_school_admission_no` on (school_id, admission_number)

### `student_enrollments`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `section_id` | INTEGER | no | FK → `sections.id` (ON DELETE CASCADE); indexed |
| `roll_number` | VARCHAR(20) | no |  |
| `enrolled_on` | DATE | no |  |
| `status` | enrollment_status | no |  |
| `remarks` | TEXT | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_enrollment_roll_per_section_session` on (session_id, class_id, section_id, roll_number)

### `student_guardians`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `guardian_id` | INTEGER | no | FK → `guardians.id` (ON DELETE CASCADE); indexed |
| `relationship_to_student` | guardian_relation | no |  |
| `is_primary_contact` | BOOLEAN | no |  |
| `is_emergency_contact` | BOOLEAN | no |  |

Constraints:

- **UNIQUE** `uq_student_guardian_pair` on (student_id, guardian_id)

### `student_documents`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `document_type` | student_document_type | no |  |
| `file_path` | VARCHAR(255) | no |  |
| `original_filename` | VARCHAR(255) | no |  |
| `uploaded_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

### `teacher_profiles`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `user_id` | INTEGER | no | FK → `users.id` (ON DELETE CASCADE); unique |
| `employee_id` | VARCHAR(40) | no |  |
| `father_or_spouse_name` | VARCHAR(120) | yes |  |
| `date_of_birth` | DATE | yes |  |
| `gender` | teacher_gender | yes |  |
| `address` | VARCHAR(255) | yes |  |
| `qualification` | VARCHAR(200) | yes |  |
| `specialization` | VARCHAR(200) | yes |  |
| `joining_date` | DATE | no |  |
| `salary` | NUMERIC(12, 2) | yes |  |
| `employment_status` | employment_status | no |  |
| `photo_path` | VARCHAR(255) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `` on (user_id)
- **UNIQUE** `uq_teacher_school_employee_id` on (school_id, employee_id)

### `staff`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `user_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL); unique |
| `employee_id` | VARCHAR(40) | no |  |
| `name` | VARCHAR(120) | no |  |
| `position` | VARCHAR(100) | no |  |
| `department` | VARCHAR(100) | yes |  |
| `phone` | VARCHAR(30) | yes |  |
| `address` | VARCHAR(255) | yes |  |
| `joining_date` | DATE | no |  |
| `salary` | NUMERIC(12, 2) | yes |  |
| `employment_status` | staff_employment_status | no |  |
| `photo_path` | VARCHAR(255) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `` on (user_id)
- **UNIQUE** `uq_staff_school_employee_id` on (school_id, employee_id)

## Attendance & leave (Phase 3)

### `student_attendance`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `section_id` | INTEGER | no | FK → `sections.id` (ON DELETE CASCADE); indexed |
| `date` | DATE | no | indexed |
| `status` | student_attendance_status | no |  |
| `remarks` | VARCHAR(255) | yes |  |
| `marked_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_student_attendance_one_per_day` on (student_id, date)

### `teacher_attendance`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `user_id` | INTEGER | no | FK → `users.id` (ON DELETE CASCADE); indexed |
| `date` | DATE | no | indexed |
| `status` | teacher_attendance_status | no |  |
| `remarks` | VARCHAR(255) | yes |  |
| `marked_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_teacher_attendance_one_per_day` on (user_id, date)

### `leave_requests`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `applicant_role` | leave_applicant_role | no | indexed |
| `student_id` | INTEGER | yes | FK → `students.id` (ON DELETE CASCADE) |
| `teacher_user_id` | INTEGER | yes | FK → `users.id` (ON DELETE CASCADE) |
| `staff_id` | INTEGER | yes | FK → `staff.id` (ON DELETE CASCADE) |
| `leave_type` | leave_type | no |  |
| `start_date` | DATE | no |  |
| `end_date` | DATE | no |  |
| `reason` | TEXT | yes |  |
| `status` | leave_status | no | indexed |
| `applied_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `approved_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `approved_on` | TIMESTAMP WITH TIME ZONE | yes |  |
| `decision_remarks` | TEXT | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_leave_exactly_one_applicant`: `(applicant_role = 'STUDENT' AND student_id IS NOT NULL AND teacher_user_id IS NULL AND staff_id IS NULL) OR (applicant_role = 'TEACHER' AND teacher_user_id IS NOT NULL AND student_id IS NULL AND staff_id IS NULL) OR (applicant_role = 'STAFF' AND staff_id IS NOT NULL AND student_id IS NULL AND teacher_user_id IS NULL)`
- **CHECK** `ck_leave_end_after_start`: `end_date >= start_date`

## Timetable (Phase 4)

### `periods`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(50) | no |  |
| `order_index` | INTEGER | no |  |
| `start_time` | TIME WITHOUT TIME ZONE | no |  |
| `end_time` | TIME WITHOUT TIME ZONE | no |  |
| `is_break` | BOOLEAN | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_period_school_name` on (school_id, name)
- **CHECK** `ck_period_end_after_start`: `end_time > start_time`
- **UNIQUE** `uq_period_school_order` on (school_id, order_index)

### `timetable_entries`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `section_id` | INTEGER | no | FK → `sections.id` (ON DELETE CASCADE); indexed |
| `period_id` | INTEGER | no | FK → `periods.id` (ON DELETE CASCADE); indexed |
| `day_of_week` | timetable_day_of_week | no | indexed |
| `subject_id` | INTEGER | yes | FK → `subjects.id` (ON DELETE SET NULL) |
| `teacher_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `room` | VARCHAR(50) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_timetable_teacher_slot` on (session_id, teacher_id, day_of_week, period_id)
- **UNIQUE** `uq_timetable_room_slot` on (session_id, room, day_of_week, period_id)
- **UNIQUE** `uq_timetable_section_slot` on (session_id, section_id, day_of_week, period_id)

## Examinations (Phase 5)

### `exams`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `class_id` | INTEGER | no | FK → `classes.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(120) | no |  |
| `exam_type` | exam_type | no |  |
| `start_date` | DATE | no |  |
| `end_date` | DATE | no |  |
| `description` | TEXT | yes |  |
| `status` | exam_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_exam_school_session_class_name` on (school_id, session_id, class_id, name)
- **CHECK** `ck_exam_end_after_start`: `end_date >= start_date`

### `exam_subjects`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `exam_id` | INTEGER | no | FK → `exams.id` (ON DELETE CASCADE); indexed |
| `subject_id` | INTEGER | no | FK → `subjects.id` (ON DELETE CASCADE); indexed |
| `max_marks` | INTEGER | no |  |
| `passing_marks` | INTEGER | no |  |
| `exam_date` | DATE | yes |  |
| `start_time` | TIME WITHOUT TIME ZONE | yes |  |
| `end_time` | TIME WITHOUT TIME ZONE | yes |  |
| `room` | VARCHAR(50) | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_exam_subject_passing_le_max`: `passing_marks <= max_marks`
- **UNIQUE** `uq_exam_subject_pair` on (exam_id, subject_id)

### `marks`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `exam_subject_id` | INTEGER | no | FK → `exam_subjects.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `obtained_marks` | NUMERIC(6, 2) | no |  |
| `remarks` | VARCHAR(255) | yes |  |
| `entered_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_mark_obtained_non_negative`: `obtained_marks >= 0`
- **UNIQUE** `uq_mark_exam_subject_student` on (exam_subject_id, student_id)

### `grade_bands`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `grade` | VARCHAR(5) | no |  |
| `min_percentage` | FLOAT | no |  |
| `max_percentage` | FLOAT | no |  |
| `order_index` | INTEGER | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_grade_band_max_ge_min`: `max_percentage >= min_percentage`

### `report_card_remarks`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `exam_id` | INTEGER | no | FK → `exams.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `teacher_remarks` | TEXT | yes |  |
| `principal_remarks` | TEXT | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_report_card_remark_exam_student` on (exam_id, student_id)

## Student fees (Phase 6)

### `fee_types`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(100) | no |  |
| `default_amount` | NUMERIC(10, 2) | yes |  |
| `is_recurring` | BOOLEAN | no |  |
| `status` | fee_type_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_fee_type_school_name` on (school_id, name)

### `student_fees`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_id` | INTEGER | no | FK → `students.id` (ON DELETE CASCADE); indexed |
| `fee_type_id` | INTEGER | no | FK → `fee_types.id` (ON DELETE RESTRICT); indexed |
| `session_id` | INTEGER | no | FK → `academic_sessions.id` (ON DELETE CASCADE); indexed |
| `amount` | NUMERIC(10, 2) | no |  |
| `due_date` | DATE | no |  |
| `notes` | TEXT | yes |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

### `fee_discounts`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_fee_id` | INTEGER | no | FK → `student_fees.id` (ON DELETE CASCADE); indexed |
| `discount_type` | discount_type | no |  |
| `value` | NUMERIC(10, 2) | no |  |
| `computed_amount` | NUMERIC(10, 2) | no |  |
| `reason` | TEXT | no |  |
| `applied_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_fee_discount_non_negative`: `computed_amount >= 0`

### `fee_payments`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `student_fee_id` | INTEGER | no | FK → `student_fees.id` (ON DELETE CASCADE); indexed |
| `receipt_number` | VARCHAR(40) | no |  |
| `amount` | NUMERIC(10, 2) | no |  |
| `payment_method` | payment_method | no |  |
| `payment_date` | DATE | no |  |
| `notes` | TEXT | yes |  |
| `received_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_fee_payment_school_receipt` on (school_id, receipt_number)
- **CHECK** `ck_fee_payment_amount_positive`: `amount > 0`

## School finance (Phase 7)

### `expense_categories`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `name` | VARCHAR(100) | no |  |
| `status` | expense_category_status | no |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **UNIQUE** `uq_expense_category_school_name` on (school_id, name)

### `expenses`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `category_id` | INTEGER | no | FK → `expense_categories.id` (ON DELETE RESTRICT); indexed |
| `description` | VARCHAR(255) | no |  |
| `amount` | NUMERIC(10, 2) | no |  |
| `expense_date` | DATE | no | indexed |
| `payment_method` | expense_payment_method | no |  |
| `vendor` | VARCHAR(150) | yes |  |
| `notes` | TEXT | yes |  |
| `recorded_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_expense_amount_positive`: `amount > 0`

### `salary_records`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | PK |
| `school_id` | INTEGER | no | FK → `schools.id` (ON DELETE CASCADE); indexed |
| `recipient_role` | salary_recipient_role | no | indexed |
| `teacher_user_id` | INTEGER | yes | FK → `users.id` (ON DELETE CASCADE) |
| `staff_id` | INTEGER | yes | FK → `staff.id` (ON DELETE CASCADE) |
| `month` | DATE | no | indexed |
| `basic_salary` | NUMERIC(10, 2) | no |  |
| `allowances` | NUMERIC(10, 2) | no |  |
| `deductions` | NUMERIC(10, 2) | no |  |
| `bonus` | NUMERIC(10, 2) | no |  |
| `payment_status` | salary_payment_status | no |  |
| `payment_date` | DATE | yes |  |
| `notes` | TEXT | yes |  |
| `generated_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `paid_by_id` | INTEGER | yes | FK → `users.id` (ON DELETE SET NULL) |
| `created_at` | TIMESTAMP WITH TIME ZONE | no |  |
| `updated_at` | TIMESTAMP WITH TIME ZONE | no |  |

Constraints:

- **CHECK** `ck_salary_exactly_one_recipient`: `(recipient_role = 'TEACHER' AND teacher_user_id IS NOT NULL AND staff_id IS NULL) OR (recipient_role = 'STAFF' AND staff_id IS NOT NULL AND teacher_user_id IS NULL)`
- **UNIQUE** `uq_salary_staff_month` on (staff_id, month)
- **CHECK** `ck_salary_amounts_non_negative`: `basic_salary >= 0 AND allowances >= 0 AND deductions >= 0 AND bonus >= 0`
- **UNIQUE** `uq_salary_teacher_month` on (teacher_user_id, month)
