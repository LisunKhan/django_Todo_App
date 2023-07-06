from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TodoItem, UserProfile


class TodoForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ['title', 'description']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic', 'date_of_birth', 'location']


class RegistrationForm(UserCreationForm):
    profile = UserProfileForm()

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        profile_data = self.cleaned_data.get('profile')
        if profile_data:
            profile = UserProfile.objects.create(user=user, **profile_data)
            user.profile = profile
        if commit:
            user.save()
        return user