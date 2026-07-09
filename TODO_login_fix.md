# TODO: Fix Login / Dashboard Redirection

## Goal
Make the login page accept username/password, authenticate the user, and redirect to the correct dashboard.

## Steps
- [ ] Inspect current `login_view` implementation (confirm it’s stubbed).
- [ ] Create a real login form (or use Django `AuthenticationForm`) to provide `form.username`, `form.password`, and optional role field.
- [ ] Implement POST handling in `schoolms/apps/accounts/views.py@login_view`:
  - [ ] Read `username/email`, `password` (and role if present)
  - [ ] Authenticate using `django.contrib.auth.authenticate()`
  - [ ] On success: call `django.contrib.auth.login()`
  - [ ] Redirect:
    - Prefer `dashboard:home` or role-specific redirect already present in project.
  - [ ] On failure: show error message and re-render form.
- [ ] Ensure CSRF + template fields render correctly.
- [ ] Stop any duplicate server instance causing port 8000 binding error (WinError 10048).
- [ ] Run server and test login flow end-to-end.

