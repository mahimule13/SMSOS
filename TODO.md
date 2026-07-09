# TODO - Exam timetable and marks entry improvements

## Step 1: Plan
- [x] Gather context from existing dashboards, templates, and exams app (done in analysis).
- [ ] Define changes needed for:
  - Student dashboard: show exam timetable filtered by student.section.
  - Teacher marks entry: tie marks entry to a specific exam schedule.

## Step 2: Implement student exam timetable
- [x] Add query to student_dashboard view to fetch `ExamSchedule` for the student's section.
- [x] Pass the fetched schedules to `dashboard/student_dashboard.html`.
- [x] Update student_dashboard template to render an “Exam Timetable” table.


## Step 3: Implement schedule-based teacher marks entry
- [x] Update exams views/forms:
  - [x] Provide teacher UI to select exam schedule (exam + section + subject).
  - [x] When saving marks, use the selected schedule’s `exam` and `subject` (not only active exam).
  - [x] Update `templates/exams/teacher_mark_entry.html` to show schedule selection.



## Step 4: Keep backward compatibility / validation
- [ ] Ensure teachers can only choose schedules for sections they teach.
- [ ] Prevent marks from being entered for mismatched exam/subject/schedule.

## Step 5: Migrations + testing
- [ ] If DB model changes are needed, create and apply migrations.
- [ ] Run Django checks and basic smoke tests.


