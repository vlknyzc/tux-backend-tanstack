from django import forms
from .models import Convention


class ConventionForm(forms.ModelForm):
    class Meta:
        model = Convention
        fields = ['workspace', 'name', 'description',
                  'status', 'valid_from', 'valid_until']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')

        if valid_until and valid_from and valid_until < valid_from:
            raise forms.ValidationError("End date must be after start date")
        return cleaned_data
