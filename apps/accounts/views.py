from django.shortcuts import render, redirect, get_object_or_404  # type: ignore[import]
from django.contrib.auth import login, logout, authenticate  # type: ignore[import]
from django.contrib.auth.decorators import login_required  # type: ignore[import]
from django.contrib.auth.models import User  # type: ignore[import]
from django.contrib import messages  # type: ignore[import]
from django.utils import timezone  # type: ignore[import]
# optional imports removed if unused
from apps.accounts.ivr_service import make_call, ParentContact, trigger_twilio_ivr_calls, _to_e164_or_none

from .models import UserProfile, PasswordReset, AuditLog

from django.views.decorators.http import require_POST  # type: ignore[import]
from django.http import JsonResponse  # type: ignore[import]


from .forms import LoginForm, UserRegistrationForm
from .decorators import role_required


def get_user_dashboard_redirect(user):
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return 'accounts:profile'

    role = profile.role

    if role in ['super_admin', 'school_admin']:
        return 'dashboard:admin_dashboard'
    if role == 'principal':
        return 'dashboard:principal_dashboard'
    if role == 'teacher':
        return 'dashboard:teacher_dashboard'
    if role == 'student':
        return 'dashboard:student_dashboard'
    if role == 'accountant':
        return 'dashboard:accountant_dashboard'
    if role == 'librarian':
        return 'dashboard:librarian_dashboard'

    return 'accounts:profile'


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def create_audit_log(user, action, module, description, request):
    AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        description=description,
        ip_address=get_client_ip(request),
    )


# =========================================================
# AUTH (currently stubbed because required forms are missing)
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect(get_user_dashboard_redirect(request.user))

    form = LoginForm()

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:

                try:
                    profile = user.profile

                    # Optional role checking
                    if role and profile.role != role:
                        messages.error(request, 'Selected role does not match user role')
                        return render(
                            request,
                            'accounts/login.html',
                            {'form': form}
                        )

                    login(request, user)

                    create_audit_log(
                        user,
                        'login',
                        'accounts',
                        'User logged in',
                        request
                    )

                    messages.success(request, 'Login successful')

                    return redirect(
                        get_user_dashboard_redirect(user)
                    )

                except UserProfile.DoesNotExist:
                    messages.error(request, 'User profile not found')

            else:
                messages.error(request, 'Invalid username or password')

    return render(
        request,
        'accounts/login.html',
        {'form': form},
    )


@login_required(login_url='accounts:login')
def logout_view(request):
    create_audit_log(
        request.user,
        'logout',
        'accounts',
        'User logged out',
        request,
    )
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect(get_user_dashboard_redirect(request.user))

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please login.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


# =========================================================
# PRINCIPAL
# =========================================================

@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin')
def add_principal(request):
    # Keep stub import-safe until UserRegistrationForm exists.
    return render(request, 'accounts/add_principal.html', {'form': None})


@login_required(login_url='accounts:login')
@role_required('principal')
def principal_create_student_credentials(request):
    from apps.students.models import Student
    from apps.classes.models import Section

    principal_name = request.user.get_full_name() or request.user.username

    def generate_unique_student_id():
        while True:
            candidate = f"STU{Student.objects.count() + 1001}"
            if not Student.objects.filter(student_id=candidate).exists():
                return candidate

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        roll_number = request.POST.get('roll_number')
        admission_number = request.POST.get('admission_number')
        section_id = request.POST.get('section')

        if not section_id:
            messages.error(request, 'Section is required')
            sections = Section.objects.all()
            return render(
                request,
                'accounts/principal_create_student_credentials.html',
                {'principal_name': principal_name, 'sections': sections},
            )

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            sections = Section.objects.all()
            return render(
                request,
                'accounts/principal_create_student_credentials.html',
                {'principal_name': principal_name, 'sections': sections},
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        UserProfile.objects.create(
            user=user,
            role='student',
            school_id=request.user.profile.school_id,
            school_name=request.user.profile.school_name,
        )

        Student.objects.create(
            user=user,
            student_id=generate_unique_student_id(),
            admission_number=admission_number,
            roll_number=roll_number,
            section_id=section_id,
        )

        messages.success(request, 'Student credentials created successfully')
        sections = Section.objects.all()

        return render(
            request,
            'accounts/principal_create_student_credentials.html',
            {
                'principal_name': principal_name,
                'sections': sections,
                'generated_credentials': {'username': username, 'password': password},
            },
        )

    sections = Section.objects.all()
    return render(
        request,
        'accounts/principal_create_student_credentials.html',
        {'principal_name': principal_name, 'sections': sections},
    )


# =========================================================
# PROFILE
# =========================================================

@login_required(login_url='accounts:login')
def profile_view(request):
    # Create the profile on-demand to avoid 404s for newly created users.
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(
        request,
        'accounts/profile.html',
        {'profile': profile, 'user': request.user},
    )



@login_required(login_url='accounts:login')
def edit_profile_view(request):
    # Stub: UserProfileForm missing in forms.py
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(
        request,
        'accounts/edit_profile.html',
        {'form': None, 'profile': profile},
    )


@login_required(login_url='accounts:login')
def change_password_view(request):
    return render(request, 'accounts/change_password.html', {'form': None})


# =========================================================
# PASSWORD RESET (existing model)
# =========================================================

def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        # Stub: ForgotPasswordForm missing
        messages.error(request, 'Forgot password form not implemented')

    return render(request, 'accounts/forgot_password.html', {'form': None})


def reset_password_view(request, token):
    try:
        reset = get_object_or_404(PasswordReset, token=token)

        if reset.is_used:
            messages.error(request, 'Reset link already used')
            return redirect('accounts:login')

        if reset.expires_at < timezone.now():
            messages.error(request, 'Reset link expired')
            return redirect('accounts:login')

        # Keep minimal implementation (no ResetPasswordForm)
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if not password1 or password1 != password2:
                messages.error(request, 'Passwords do not match')
            else:
                user = reset.user
                user.set_password(password1)
                user.save()
                reset.is_used = True
                reset.save()
                messages.success(request, 'Password reset successful')
                return redirect('accounts:login')

        return render(request, 'accounts/reset_password.html', {'token': token})

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset link')
        return redirect('accounts:login')


# =========================================================
# STATIC PAGES
# =========================================================

def index(request):
    return render(request, 'accounts/index.html')


def smsabout(request):
    return render(request, 'accounts/smsabout.html')


def services(request):
    return render(request, 'accounts/services.html')


def pricing(request):
    return render(request, 'accounts/pricng.html')


def smsstudent(request):
    return render(request, 'accounts/smsstudent.html')


def smsteacher(request):
    return render(request, 'accounts/smsteacher.html')
def smsparent(request):

    from apps.students.models import Student
    from .forms import BulkSMSForm
    from .services import SmsRecipient, send_parent_bulk_sms

    selected_student_ids = []

    # =========================
    # FILTER STUDENTS
    # =========================

    student_filter = request.POST.get('student_filter', 'all')

    if student_filter == 'pending':

        students = Student.objects.filter(
            is_active=True,
            fee_collections__status__in=['pending', 'partial']
        ).select_related('user').distinct()

    else:

        students = Student.objects.filter(
            is_active=True
        ).select_related('user')

    # =========================
    # POST REQUEST
    # =========================

    if request.method == 'POST':

        form = BulkSMSForm(request.POST)

        action = request.POST.get('action')

        # Selected students
        for sid in request.POST.getlist('student_ids'):

            try:
                selected_student_ids.append(int(sid))

            except Exception:
                continue

        # Selected contacts
        selected_contact_values = request.POST.getlist(
            'contact_phone'
        )

        selected_students = list(
            Student.objects.filter(
                id__in=selected_student_ids,
                is_active=True
            ).select_related('section', 'user')
        )

        # =========================
        # LOAD STUDENTS
        # =========================

        if action in ['load_students', 'load']:

            return render(
                request,
                'accounts/smsparent.html',
                {
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                    'selected_students': [],
                    'selected_contact_values': selected_contact_values,
                    'student_filter': student_filter,
                    'form': form,
                },
            )

        # =========================
        # SHOW CONTACTS
        # =========================

        if action == 'show_contacts':

            return render(
                request,
                'accounts/smsparent.html',
                {
                    'students': students,
                    'selected_student_ids': selected_student_ids,
                    'selected_students': selected_students,
                    'student_filter': student_filter,
                    'form': form,
                    'selected_contact_values': selected_contact_values,
                },
            )

        # =========================
        # SEND SMS
        # =========================

        if action == 'send_sms':

            if not selected_student_ids:

                messages.error(
                    request,
                    'Select at least one student.'
                )

            elif not selected_contact_values:

                messages.error(
                    request,
                    'Select at least one contact phone.'
                )

            elif not form.is_valid():

                messages.error(
                    request,
                    'Invalid message data.'
                )

            else:

                message_template = form.cleaned_data.get(
                    'message',
                    ''
                )

                recipients = []

                student_map = {
                    s.id: s for s in selected_students
                }

                for value in selected_contact_values:

                    try:

                        kind, sid_str = value.split(':', 1)

                        sid = int(sid_str)

                    except Exception:
                        continue

                    s = student_map.get(sid)

                    if not s:
                        continue

                    # =========================
                    # FATHER
                    # =========================

                    if (
                        kind == 'father'
                        and s.father_phone
                    ):

                        recipients.append(
                            SmsRecipient(
                                phone=s.father_phone,
                                name=s.father_name,
                            )
                        )

                    # =========================
                    # MOTHER
                    # =========================

                    elif (
                        kind == 'mother'
                        and s.mother_phone
                    ):

                        recipients.append(
                            SmsRecipient(
                                phone=s.mother_phone,
                                name=s.mother_name,
                            )
                        )

                    # =========================
                    # GUARDIAN
                    # =========================

                    elif (
                        kind == 'guardian'
                        and s.guardian_phone
                    ):

                        recipients.append(
                            SmsRecipient(
                                phone=s.guardian_phone,
                                name=s.guardian_name or 'Guardian',
                            )
                        )

                # =========================
                # NO RECIPIENTS
                # =========================

                if not recipients:

                    messages.error(
                        request,
                        'No valid phone numbers found.'
                    )

                else:

                    result = send_parent_bulk_sms(
                        recipients=recipients,
                        template=message_template,
                        extra_context={},
                    )

                    messages.success(
                        request,
                        f"SMS completed. "
                        f"Sent: {result.get('sent', 0)}"
                    )

        return render(
            request,
            'accounts/smsparent.html',
            {
                'students': students,
                'selected_student_ids': selected_student_ids,
                'selected_students': selected_students,
                'student_filter': student_filter,
                'selected_contact_values': selected_contact_values,
                'form': form,
            },
        )

    # =========================
    # GET REQUEST
    # =========================

    return render(
        request,
        'accounts/smsparent.html',
        {
            'students': students,
            'selected_student_ids': [],
            'selected_students': [],
            'student_filter': student_filter,
            'selected_contact_values': [],
            'form': BulkSMSForm(),
        },
    )
def smslibrary(request):
    return render(request, 'accounts/smslibrary.html')


def smsfee(request):
    return render(request, 'accounts/smsfee.html')


def smsanalytic(request):
    return render(request, 'accounts/smsanalytic.html')


# =========================================================
# IVR VOICE CALLS (Teacher Dashboard buttons)
# =========================================================

@login_required(login_url='accounts:login')
@role_required('teacher')
def fee_pending_calls(request):
    """Backward-compatible button (now redirects via old flow).

    The improved Pending Fee IVR UI uses new JSON endpoints and does not rely on this.
    """
    if request.method != 'POST':
        return redirect('dashboard:teacher_dashboard')

    # Trigger the new implementation and redirect back.
    # Keep behavior compatible with existing button.
    from apps.fees.models import FeeCollection
    from apps.students.models import Student

    fee_students = (
        FeeCollection.objects.filter(status__in=['pending', 'partial'])
        .values_list('student_id', flat=True)
        .distinct()
    )

    students = (
        Student.objects.filter(id__in=fee_students, is_active=True)
        .select_related('user')
        .distinct()
    )

    # Dedup + call all using existing make_call()
    unique_numbers: set[str] = set()
    phone_numbers: list[str] = []

    for s in students:
        for phone in [getattr(s, 'father_phone', None), getattr(s, 'mother_phone', None)]:
            if not phone:
                continue
            phone_str = str(phone).strip()
            if not phone_str:
                continue
            if phone_str in unique_numbers:
                continue
            unique_numbers.add(phone_str)
            phone_numbers.append(phone_str)

    message = "Dear Parent, your child fee payment is pending."

    failed = []
    for phone in phone_numbers:
        try:
            make_call(phone, message)
        except Exception as e:
            failed.append((phone, str(e)))
            print(f"[fee_pending_calls] Failed IVR call for {phone}: {e}")

    if failed:
        messages.success(
            request,
            f"Pending fee calls triggered. Some calls failed: {len(failed)}."
        )
    else:
        messages.success(request, "Pending fee calls triggered successfully.")

    return redirect('dashboard:teacher_dashboard')




@login_required(login_url='accounts:login')
@role_required('teacher')
def absent_calls(request):
    """Call parent(s) for students absent today."""
    if request.method != 'POST':
        return redirect('dashboard:teacher_dashboard')

    from datetime import date
    from apps.students.models import Student, StudentAttendance

    today = date.today()
    absent_student_ids = StudentAttendance.objects.filter(
        date=today,
        is_present=False,
    ).values_list('student_id', flat=True)

    students = (
        Student.objects.filter(id__in=absent_student_ids, is_active=True)
        .select_related('user')
        .distinct()
    )

    from apps.accounts.ivr_service import ParentContact, trigger_twilio_ivr_calls

    contacts: list[ParentContact] = []
    for s in students:
        contacts.append(ParentContact(phone=s.father_phone, name=s.father_name))
        if s.mother_phone:
            contacts.append(ParentContact(phone=s.mother_phone, name=s.mother_name))
        if s.guardian_phone:
            contacts.append(ParentContact(phone=s.guardian_phone, name=s.guardian_name))

    message = "Dear Parent, your child is absent today."
    trigger_twilio_ivr_calls(contacts=contacts, message=message)
    return redirect('dashboard:teacher_dashboard')


@login_required(login_url='accounts:login')
@role_required('teacher')
def general_calls(request):
    """Call parent(s) with a general school update."""
    if request.method != 'POST':
        return redirect('dashboard:teacher_dashboard')

    from apps.students.models import Student

    students = Student.objects.filter(is_active=True).select_related('user').distinct()

    from apps.accounts.ivr_service import ParentContact, trigger_twilio_ivr_calls

    contacts: list[ParentContact] = []
    for s in students:
        contacts.append(ParentContact(phone=s.father_phone, name=s.father_name))
        if s.mother_phone:
            contacts.append(ParentContact(phone=s.mother_phone, name=s.mother_name))
        if s.guardian_phone:
            contacts.append(ParentContact(phone=s.guardian_phone, name=s.guardian_name))

    message = "Dear Parent, please check the latest school updates."
    trigger_twilio_ivr_calls(contacts=contacts, message=message)
    return redirect('dashboard:teacher_dashboard')


# =========================================================
# Pending Fee IVR - JSON endpoints for dynamic UI
# =========================================================

import json
from decimal import Decimal


def _get_session_called_numbers(request) -> set[str]:
    key = 'ivr_called_numbers'
    val = request.session.get(key) or []
    if isinstance(val, list):
        return set(val)
    if isinstance(val, set):
        return set(val)
    return set()


def _save_session_called_numbers(request, numbers: set[str]):
    request.session['ivr_called_numbers'] = sorted(list(numbers))


def _mark_numbers_called(request, numbers: set[str]):
    called = _get_session_called_numbers(request)
    called |= set(numbers)
    _save_session_called_numbers(request, called)


def _normalize_phone_for_session(phone):
    if not phone:
        return None
    return _to_e164_or_none(str(phone).strip())


def _get_teacher_fee_rows_for_call():
    # Placeholder to keep code organized; data comes from DB models directly
    return None


@login_required(login_url='accounts:login')
@role_required('teacher')
@require_POST
def call_parent_for_fee_student(request):
    """Call father and mother for a single FeeCollection row.

    Returns JSON for dynamic UI updates.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = request.POST.dict()

    fee_collection_id = payload.get('fee_collection_id')
    if not fee_collection_id:
        return JsonResponse({'ok': False, 'error': 'fee_collection_id required'}, status=400)

    from apps.fees.models import FeeCollection

    fc = get_object_or_404(FeeCollection, id=fee_collection_id)
    student = fc.student

    # Skip empty numbers
    father_phone = getattr(student, 'father_phone', '')
    mother_phone = getattr(student, 'mother_phone', '')

    contacts: list[ParentContact] = []

    for phone, name in [(father_phone, getattr(student, 'father_name', 'Father')), (mother_phone, getattr(student, 'mother_name', 'Mother'))]:
        normalized = _normalize_phone_for_session(phone)
        if normalized:
            contacts.append(ParentContact(phone=normalized, name=name))

    called_numbers = _get_session_called_numbers(request)

    # For status: treat phones already marked as already-called, don't trigger them.
    to_trigger_contacts: list[ParentContact] = []
    already_called: list[str] = []
    for c in contacts:
        if c.phone in called_numbers:
            already_called.append(c.phone)
        else:
            to_trigger_contacts.append(c)

    message = "Dear Parent, your child fee payment is pending." 

    results = []
    attempted = 0
    success = 0
    failed = 0
    failed_reasons = []

    if to_trigger_contacts:
        # trigger_twilio_ivr_calls returns per-number results but already normalizes/dedupes.
        try:
            trigger_out = trigger_twilio_ivr_calls(contacts=to_trigger_contacts, message=message)
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'fee_collection_id': int(fee_collection_id),
                'already_called': already_called,
                'error': str(e),
                'results': [],
                'attempted': 0,
                'success': 0,
                'failed': 0,
                'failed_reasons': [],
            }, status=500)

        attempted = trigger_out.get('attempted') or 0
        results = trigger_out.get('results') or []
        success = trigger_out.get('successful_calls') or 0
        failed = max(attempted - success, 0)

        for r in results:
            if r and r.get('status') == 'FAILED':
                fr = r.get('failure_reason') or r.get('twilio_error_message') or r.get('error')
                if fr:
                    failed_reasons.append(fr)

        # Mark successful calls as called based on returned phone list.
        # NOTE: trigger_twilio_ivr_calls() normalizes phones to E.164 before calling,
        # so we must store the normalized numbers to keep session matching consistent.
        success_phones = {r.get('phone') for r in results if r.get('status') == 'SUCCESS' and r.get('phone')}
        _mark_numbers_called(request, success_phones)




    response = {
        'ok': True,
        'fee_collection_id': int(fee_collection_id),
        'already_called': already_called,
        'results': results,
        'attempted': attempted,
        'success': success,
        'failed': failed,
        'failed_reasons': sorted(list(set(failed_reasons))),
    }
    return JsonResponse(response)


@login_required(login_url='accounts:login')
@role_required('teacher')
@require_POST
def call_all_pending_fee_parents(request):
    """Call father+mother for all pending/partial FeeCollection rows.

    Returns JSON for dynamic UI updates.
    """
    from apps.fees.models import FeeCollection

    called_numbers = _get_session_called_numbers(request)

    pending_qs = (
        FeeCollection.objects.filter(status__in=['pending', 'partial'])
        .select_related('student', 'fee_structure')
        .order_by('-month')
    )

    contacts: list[ParentContact] = []
    for fc in pending_qs:
        student = fc.student
        father_phone = getattr(student, 'father_phone', '')
        mother_phone = getattr(student, 'mother_phone', '')

        normalized_father = _normalize_phone_for_session(father_phone)
        if normalized_father:
            contacts.append(ParentContact(phone=normalized_father, name=getattr(student, 'father_name', 'Father')))

        normalized_mother = _normalize_phone_for_session(mother_phone)
        if normalized_mother:
            contacts.append(ParentContact(phone=normalized_mother, name=getattr(student, 'mother_name', 'Mother')))

    # Decide already-called vs to_trigger.
    to_trigger: list[ParentContact] = []
    already_called_set: set[str] = set()
    for c in contacts:
        if c.phone in called_numbers:
            already_called_set.add(c.phone)
        else:
            to_trigger.append(c)

    message = "Dear Parent, your child fee payment is pending." 

    results = []
    attempted = 0
    success = 0
    failed = 0
    failed_reasons = []

    if to_trigger:
        try:
            trigger_out = trigger_twilio_ivr_calls(contacts=to_trigger, message=message)
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'already_called': sorted(list(already_called_set)),
                'error': str(e),
                'results': [],
                'attempted': 0,
                'success': 0,
                'failed': 0,
                'failed_reasons': [],
            }, status=500)

        attempted = trigger_out.get('attempted') or 0
        results = trigger_out.get('results') or []
        success = trigger_out.get('successful_calls') or 0
        failed = max(attempted - success, 0)

        for r in results:
            if r and r.get('status') == 'FAILED':
                fr = r.get('failure_reason') or r.get('twilio_error_message') or r.get('error')
                if fr:
                    failed_reasons.append(fr)

        # Mark successful calls as called based on returned phone list.
        success_phones = {r.get('phone') for r in results if r.get('status') == 'SUCCESS'}
        _mark_numbers_called(request, success_phones)


    response = {
        'ok': True,
        'already_called': sorted(list(already_called_set)),
        'attempted': attempted,
        'success': success,
        'failed': failed,
        'results': results,
        'failed_reasons': sorted(list(set(failed_reasons))),
    }
    return JsonResponse(response)
