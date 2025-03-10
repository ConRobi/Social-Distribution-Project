from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Author

class AuthorRegistrationForm(UserCreationForm):
    display_name = forms.CharField(max_length=255)
    github = forms.URLField(assume_scheme="https")  # ✅ Fix for Django 6.
    profile_image = forms.URLField(required=False, assume_scheme="https")  # ✅ Fix for Django 6.0

    class Meta:
        model = Author
        # Required fields for sign up
        fields = ['username', 'display_name', 'github', 'profile_image', 'password1', 'password2']

    def save(self, commit=True):
        author = super().save(commit=False)
        author.set_password(self.cleaned_data['password1'])  # Hash the password
        if commit:
            author.save()
        return author
