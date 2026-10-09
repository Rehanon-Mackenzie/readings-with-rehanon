from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class AvailabilitySlot(models.Model):
    """A time when the reader is available to give a reading."""
    
    start_time = models.DateTimeField(unique=True)
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        start = timezone.localtime(self.start_time)
        end = timezone.localtime(self.end_time)
        return f"{start:%a %d %b %y, %H:%M} to {end:%H:%M}"
    
    def clean(self):
        """Check the slot makes sense before it is saved."""
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError(
                {'end_time': 'The end time must be after the start time.'})
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError(
                {'start_time': 'Slot cannot be added in the past.'})