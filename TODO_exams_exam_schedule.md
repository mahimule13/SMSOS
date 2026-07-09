# TODO: Fix ExamSchedule DB error + add weekly time creation

- [ ] Fix mismatch causing `no such column: exams_examschedule.section_id` by aligning Django model with actual DB schema.
- [ ] Verify current SQLite schema for `exams_examschedule` table and compare with `apps/exams/models.py`.
- [ ] Update `apps/exams/models.py` (and/or views) so field names match the real column names.
- [ ] Create a migration (or a safe data-migration plan) to update schema.
- [ ] Update any queries that reference `section_id` to use the correct FK field/related name.
- [ ] Implement weekly exam timetable time creation (teacher UI + saving to DB).
- [ ] Ensure marks entry and student reportcard still work with the new schedule structure.
- [ ] Run Django checks + migrations + manual flow test for:
  - [ ] POST `/exams/teacher/exam-schedule/create/`
  - [ ] weekly time creation for students
  - [ ] teacher marks entry using schedule

