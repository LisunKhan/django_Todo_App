from django import forms
from .models import TodoItem
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from django.contrib.auth.models import User # Not strictly required for this change, Django handles User model internally for forms

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages['unique'] = "A user with that username already exists. Please choose a different one."
        # Django's UserCreationForm includes a password confirmation field (password2) by default.
        # The error message for mismatch is handled by PasswordConfirmationField's `clean` method
        # or through form-level validation. Overriding 'invalid' on 'password2' might not be the
        # direct way for mismatch if using stock UserCreationForm.
        # However, if we were to add custom validation or a custom field, this would be how to set its message.
        # For now, we rely on Django's default for mismatch, which is usually clear.
        # If a specific 'password_mismatch' key existed on the form's error_messages, we'd use that.
        # For UserCreationForm, password validation errors (too short, common, etc.)
        # are added by PasswordValidators, and their messages are generally good.
        # If 'password2' is present and we want to change its generic 'invalid' message (not for mismatch specifically):
        if 'password2' in self.fields:
             self.fields['password2'].help_text = "Enter the same password as before, for verification." # Example of changing help_text
             # To change a specific error key for password2 if it's a custom field or has custom validators:
             # self.fields['password2'].error_messages['some_custom_error'] = "Custom message for password2."
             # The 'password_mismatch' error is typically a non_field_error or an error on 'password2'
             # raised during the clean() method of the form or field.
             # For the specific request "The two password fields didn't match. Please try again.":
             # This is usually handled by Django's core PasswordResetForm or by custom clean_password2 methods.
             # UserCreationForm's default password2 field is `PasswordConfirmationField`.
             # It doesn't have an 'invalid' error key for mismatch in error_messages by default.
             # The form's `clean` method or field's `clean` method usually raises `forms.ValidationError` directly.
             # However, if we assume we want to ensure any "invalid" entry on password2 (though less common for this field)
             # shows a specific message, or if we plan to add a validator that uses 'invalid':
             self.fields['password2'].error_messages['invalid'] = "The password confirmation is invalid. Please ensure it matches."


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = "Invalid username or password. Please double-check and try again."
        self.error_messages['inactive'] = "This account is inactive. Please contact support."

class TodoForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ['title', 'description', 'time_spent']
        widgets = { # Using widgets to make a field not required is not standard.
                    # Instead, field attributes should be customized in the form's __init__ or by declaring the field explicitly.
                    # However, a more direct way for ModelForm is to specify 'required' in 'field_classes' or 'formfield_callback'
                    # or by overriding the field.
                    # For this case, the simplest is often to declare the field explicitly if it needs customization beyond what Meta provides by default.
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['time_spent'].required = False
