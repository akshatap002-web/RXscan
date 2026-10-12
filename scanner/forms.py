import os

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Prescription


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Full name", max_length=60)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")


class UploadForm(forms.ModelForm):
    manual_text = forms.CharField(
        label="Type the prescription instead (optional)", required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Tab. Paracetamol 500 mg\n1-0-1  5 days"}),
        help_text="Use this only if the scanner can't read your image. One medicine per line.")

    class Meta:
        model = Prescription
        fields = ("image", "age_group", "conditions", "allergies")
        labels = {"image": "Prescription file", "age_group": "Patient age group"}
        widgets = {
            "conditions": forms.TextInput(attrs={"placeholder": "e.g. asthma, kidney disease"}),
            "allergies": forms.TextInput(attrs={"placeholder": "e.g. penicillin"}),
        }

    def clean_image(self):
        f = self.cleaned_data["image"]
        if os.path.splitext(f.name)[1].lower() not in (".jpg", ".jpeg", ".png", ".pdf"):
            raise forms.ValidationError("Upload a JPG, PNG or PDF file.")
        if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f"File is larger than {settings.MAX_UPLOAD_MB} MB.")
        return f
