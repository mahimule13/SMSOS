from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(*roles):
    """Decorator to check if user has required role"""

    def decorator(func):

        @wraps(func)
        def wrapper(request, *args, **kwargs):

            # Check login
            if not request.user.is_authenticated:
                messages.error(request, "Please login first")
                return redirect('accounts:login')

            try:
                # Get user role safely
                user_role = request.user.profile.role

                # Convert roles to lowercase
                allowed_roles = [role.lower() for role in roles]

                # Compare safely (normalize whitespace/case)
                user_role = str(user_role).strip().lower()
                if user_role not in allowed_roles:

                    messages.error(request, "Access Denied")
                    return redirect('accounts:profile')

            except Exception as e:
                print(e)
                messages.error(request, "Profile Error")
                return redirect('accounts:profile')

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def superadmin_required(func):
    """Decorator to check if user is superadmin"""

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        try:
            if request.user.profile.role.lower() != 'super_admin':
                messages.error(request, "Access Denied")
                return redirect('accounts:profile')

        except Exception as e:
            print(e)
            return redirect('accounts:profile')

        return func(request, *args, **kwargs)

    return wrapper


def admin_required(func):
    """Decorator to check if user is admin"""

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        try:
            allowed_roles = ['super_admin', 'school_admin']

            if request.user.profile.role.lower() not in allowed_roles:
                messages.error(request, "Access Denied")
                return redirect('accounts:profile')

        except Exception as e:
            print(e)
            return redirect('accounts:profile')

        return func(request, *args, **kwargs)

    return wrapper