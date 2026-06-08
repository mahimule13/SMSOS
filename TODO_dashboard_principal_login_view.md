# TODO: Change Principal Dashboard view to open logins / see model

## Information gathered
- Principal dashboard URL: `dashboard/principal/` -> `schoolms/apps/dashboard/views.py::principal_dashboard`
- Template: `schoolms/templates/dashboard/principal_dashboard.html`
- Navigation/sidebar is rendered in `schoolms/templates/base/layout.html`.
- Authentication/login UI is in `schoolms/templates/accounts/login.html` and login is wired through `schoolms/apps/accounts/views.py::login_view`.

## Plan
1. Identify what the user means by “open the logins / see model”:
   - Create a Principal dashboard section that links to relevant login/model-related views (likely user accounts / profile setup pages).
2. Find any existing views/URLs for listing logins or accessing account models.
   - Search in `apps/accounts/urls.py` and `apps/accounts/views.py` for list/admin pages.
3. Update principal dashboard template (`principal_dashboard.html`) to add buttons/links.
4. If no view exists, create a minimal view+URL+template to “see logins” (e.g., list `UserProfile` for principal’s school).
5. Ensure proper access control using `@role_required('principal')`.
6. Run Django checks/migrations only if needed.

## Notes
- If “logins” means “Student/Teacher credentials”, principal already has a button to `accounts:setup_student`.
- Might need a new link to principal’s login-model page (UserProfile list) or to create principal credentials.

