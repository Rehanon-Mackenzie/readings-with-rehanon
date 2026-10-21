from datetime import date, timedelta

from django import forms
from django.utils import timezone
from django.db.models import DurationField, ExpressionWrapper, F

from .models import AvailabilitySlot, Booking


def available_slots_for(reading):
    """Free, future slots that are long enough for this reading."""
    return AvailabilitySlot.objects.annotate(
        length=ExpressionWrapper(
            F('end_time') - F('start_time'), output_field=DurationField())
    ).filter(
        is_booked=False,
        start_time__gt=timezone.now(),
        length__gte=timedelta(minutes=reading.duration_minutes),
    )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['slot', 'birth_date',
                  'birth_time', 'birth_place', 'question']
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

    def __init__(self, *args, reading, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slot'].queryset = available_slots_for(reading)
        self.fields['slot'].empty_label = 'Choose a date and time'

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if birth_date > date.today():
            raise forms.ValidationError(
                "Date of birth can't be in the future?")
        return birth_date


class RescheduleForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['slot']
        labels = {'slot': 'New date and time'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slot'].queryset = available_slots_for(
            self.instance.reading_type)
        self.fields['slot'].empty_label = 'Choose a new date and time'


class SlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['start_time', 'end_time']
        labels = {'start_time': 'Starts', 'end_time': 'Ends'}
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
