"""
Forms package initialization.
This module imports and exposes all form classes used in the application.
"""

from .auth_forms import (
    LoginForm, RegistrationForm, PasswordResetForm,
    TwoFactorForm, Enable2FAForm
)
from .employee_forms import (
    EmployeeProfileForm,
    EmployeeProfileEditForm,
    DocumentUploadForm,
    FamilyMemberForm,
    JoiningForm
)
from .employer_forms import (
    EmployerProfileForm,
    EmployerProfileEditForm,
    EmployeeSearchForm,
    NewsUpdateForm
)
from .client_forms import ClientForm

__all__ = [
    'LoginForm',
    'RegistrationForm',
    'PasswordResetForm',
    'TwoFactorForm',
    'Enable2FAForm',
    'EmployeeProfileForm',
    'EmployeeProfileEditForm',
    'DocumentUploadForm',
    'FamilyMemberForm',
    'JoiningForm',
    'EmployerProfileForm',
    'EmployerProfileEditForm',
    'EmployeeSearchForm',
    'NewsUpdateForm',
    'ClientForm'
]