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
    time_spent_hours = forms.FloatField(label="Time Spent (hours)", required=False)
    task_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = TodoItem
        # Include all model fields that the form should handle directly or indirectly.
        # 'time_spent' is the actual model field.
        fields = ['title', 'description', 'project', 'status', 'task_date']

    def __init__(self, *args, **kwargs):
        # Pop 'user' from kwargs before calling super(), as ModelForm doesn't expect it.
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs) # Populates self.initial for fields in Meta.fields

        if user:
            from .models import Project # Local import to avoid circular dependency if Project model imports forms
            from django.db.models import Q # For OR queries
            # Filter projects to those owned by or member of the user
            user_projects = Project.objects.filter(
                Q(owner=user) | Q(members=user)
            ).distinct().order_by('name')
            self.fields['project'].queryset = user_projects

        # Set the initial value for 'time_spent_hours' in the form's initial data dictionary.
        if self.instance and self.instance.pk and self.instance.time_spent is not None:
            self.initial['time_spent_hours'] = self.instance.time_spent_hours
        else:
            # Provide a default for time_spent_hours if no instance or time_spent is None
            self.initial['time_spent_hours'] = self.fields['time_spent_hours'].initial if self.fields['time_spent_hours'].initial is not None else 0

        # Make status not required in the form, model default will be used
        self.fields['status'].required = False
        # Set initial for status if it's a new form and status is not already in initial data
        # This helps the form display the default value even before saving.
        if not self.initial.get('status') and not (self.instance and self.instance.pk):
            self.initial['status'] = 'todo' # Corresponds to model default


    def clean_time_spent_hours(self):
        hours = self.cleaned_data.get('time_spent_hours')
        if hours is None:
            return 0  # Default to 0 if not provided
        if hours < 0:
            raise forms.ValidationError("Time spent cannot be negative.")
        return hours

    def save(self, commit=True):
        # Get the hours from the cleaned data
        hours = self.cleaned_data.get('time_spent_hours', 0)
        # Convert hours to minutes and set it on the instance
        self.instance.time_spent = int((hours or 0) * 60)

        # Call the superclass's save method to save the instance
        # but ensure 'time_spent_hours' is not passed to the model's constructor
        # if it's not a model field.
        # Since 'time_spent_hours' is not a model field, we should pop it
        # if we were directly passing self.cleaned_data to model.
        # However, ModelForm's save() handles this by only using fields that exist on the model.
        return super().save(commit)


from .models import UserProfile # Import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile # Corrected model
        fields = ['bio', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].widget.attrs.update({'rows': 3, 'placeholder': 'Tell us a bit about yourself...'})
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control-file'})

        # Make fields not required by default, as users may not want to update all fields at once
        self.fields['bio'].required = False
        self.fields['profile_picture'].required = False
