from datetime import date

from django import forms
from django.utils import timezone

from .models import AvailabilitySlot, Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['slot', 'birth_date', 'birth_time', 'birth_place', 'question']
        labels = {
            'slot': 'Date and time',
            'birth_date': 'Date of birth',
            'birth_place': 'Place of birth',
            'question': 'Anything you would like me to focus on?'
        }
        help_texts = {
            'birth_date': 'Booking as a gift? Enter their birth details instead.',
            'birth_time': 'Optional, but it makes the reading more accurate.',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'birth_time': forms.TimeInput(attrs={'type': 'time'}),
            'question': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer free, future slots. This is set here (not in Meta)
        # So "now" is worked out each time the form is made.
        self.fields['slot'].queryset = AvailabilitySlot.objects.filter(
            is_booked=False, start_time__gt=timezone.now())
        self.fields['slot'].empty_label = 'Choose a date and time'

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if birth_date > date.today():
            raise forms.ValidationError("Date of birth can't be in the future?")
        return birth_date
