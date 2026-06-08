# TODO_dashboard_principal_properly

## Status
- [x] Update `principal_dashboard` view to include missing analytics context for charts.

## Remaining work
- [ ] Update `schoolms/templates/dashboard/principal_dashboard.html` to render the full analytics chart sections (copy from `admin_dashboard.html`).
- [x] Fix the announcement/leave-card layout structure in `principal_dashboard.html`.
- [ ] Ensure template variable names match:
  - `attendance_data`, `teacher_attendance_data`, `fee_data`, `teacher_gender_data`, `class_distribution_data`.
- [ ] Final sanity: load principal dashboard and confirm no missing-context errors.


