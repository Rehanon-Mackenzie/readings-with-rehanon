from django import forms

from .models import ReadingType


class ReadingTypeForm(forms.ModelForm):
    """Form for the site owner to add and edit readings."""

    class Meta:
        model = ReadingType
        fields = [
            'name', 'summary', 'description', 'price',
            'duration_minutes', 'image', 'is_active',
        ]
        labels = {
            'duration_minutes': 'Duration (minutes)',
            'is_active': 'Show this reading on the site',
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('The price must be more than £0.')
        return price

    def clean_duration_minutes(self):
        duration = self.cleaned_data['duration_minutes']
        if duration < 15 or duration > 180:
            raise forms.ValidationError('Readings must be between 15 and 180 minutes long.')
        return duration
