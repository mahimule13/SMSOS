# TODO: Fix principal creates student credentials

- [x] Update `principal_create_student_credentials` view to:
  - [x] Pass `principal_name` and `generated_credentials` to template.
  - [x] Re-render the same page on POST to show generated credentials immediately.
  - [x] Fix `student_id` generation to avoid collisions.
- [x] Ensure template receives required context variables after POST success.
- [ ] Basic manual test:
  - [ ] Principal logs in
  - [ ] Create student credentials
  - [ ] Credentials appear on the same page
  - [ ] student_id uniqueness confirmed


