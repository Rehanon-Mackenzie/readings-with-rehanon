from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from readings.models import ReadingType


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


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookings')
    reading_type = models.ForeignKey(
        ReadingType, on_delete=models.PROTECT, related_name='bookings')
    slot = models.ForeignKey(
        AvailabilitySlot, on_delete=models.PROTECT, related_name='bookings')
    birth_date = models.DateField()
    birth_time = models.TimeField(null=True, blank=True)
    birth_place = models.CharField(max_length=100)
    question = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['slot__start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['slot'],
                condition=~Q(status='cancelled'),
                name='one_active_booking_per_slot',
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.reading_type.name} - {self.slot}"