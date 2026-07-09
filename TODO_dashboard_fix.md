# TODO - Admin dashboard charts + Add Student username/password

## Completed
- Identified missing chart datasets provided by `admin_dashboard()`.
- Updated `admin_dashboard()` to compute chart datasets (attendance, fee, class distribution, teacher attendance, teacher gender) and provide `sections/selected_section` + safe defaults.
- Updated `templates/students/create.html` to include username/password/password2 fields.

## Remaining (must fix)
- `schoolms/apps/students/views.py::create_student()` currently has indentation/syntax issues after previous edits. Re-write the POST handler cleanly so it:
  - validates password==password2
  - checks username uniqueness (if provided)
  - creates user with `create_user(..., password=password)`
  - creates `Student` + `UserProfile`
  - creates `FeeCollection` when fee structure selected

## Testing
- Run Django server and verify:
  - Admin dashboard renders all Chart.js graphs without JS console errors.
  - Add Student form saves a usable login password.

