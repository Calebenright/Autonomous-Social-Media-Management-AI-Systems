from django import forms
from .models import UserSettings

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['business_description', 'website', 'brand_color', 'logo', 'temperature']

