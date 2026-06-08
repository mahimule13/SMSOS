from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


# ==========================================
# USER REGISTRATION FORM
# ==========================================

class UserRegistrationForm(UserCreationForm):

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }
        )
    )

    role = forms.ChoiceField(
        choices=[('', 'Select Role')] + list(UserProfile.USER_ROLES),
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )

    school_id = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter school ID'
            }
        )
    )

    school_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter school name'
            }
        )
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }
        )
    )

    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Gender')] + list(UserProfile.GENDER_CHOICES),
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )

    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            }
        )
    )

    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }
        )
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }
        )
    )

    state = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter state'
            }
        )
    )

    country = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter country'
            }
        )
    )

    zip_code = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter ZIP code'
            }
        )
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
            'role',
            'school_id',
            'school_name',
            'phone',
            'gender',
            'dob',
            'photo',
            'address',
            'city',
            'state',
            'country',
            'zip_code',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter first name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter last name'})
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data.get('role', ''),
                school_id=self.cleaned_data.get('school_id') or '',
                school_name=self.cleaned_data.get('school_name') or '',
                phone=self.cleaned_data.get('phone') or '',
                gender=self.cleaned_data.get('gender') or '',
                dob=self.cleaned_data.get('dob'),
                photo=self.cleaned_data.get('photo'),
                address=self.cleaned_data.get('address') or '',
                city=self.cleaned_data.get('city') or '',
                state=self.cleaned_data.get('state') or '',
                country=self.cleaned_data.get('country') or '',
                zip_code=self.cleaned_data.get('zip_code') or '',
            )
        return user


# ==========================================
# LOGIN FORM
# ==========================================

class LoginForm(forms.Form):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter password'
            }
        )
    )

    role = forms.ChoiceField(
        choices=[('', 'Select Role (Optional)')] + list(UserProfile.USER_ROLES),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )


# ==========================================
# BULK SMS FORM
# ==========================================

class BulkSMSForm(forms.Form):

    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5
            }
        ),
        help_text="Use {name} placeholder for parent name (optional).",
        label="SMS Message",
    )

    phones_csv = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Comma/newline separated numbers"
            }
        ),
        required=False,
        help_text="Paste parent mobile numbers separated by comma or new line.",
        label="Parent mobile numbers (optional)",
    )


def parse_phones_csv(phones_csv: str) -> list[str]:

    if not phones_csv:
        return []

    parts = []

    for chunk in phones_csv.replace("\n", ",").split(","):

        p = chunk.strip()

        if p:
            parts.append(p)

    return parts