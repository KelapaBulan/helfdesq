from django import forms
from .models import Ticket
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "department", "priority", "description","contact_email"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Briefly describe your issue"
            }),
            "department": forms.Select(attrs={
                "class": "form-select"
            }),
            "priority": forms.Select(attrs={
                "class": "form-select"
            }),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe the issue in detail..."
            }),
        }
        
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter username"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes to password fields
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter password"
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm password"
        })