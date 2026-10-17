from django.db import models

import uuid

from bookings.models import Booking


class Order(models.Model):
    """A successful payment for one booking"""

    booking = models.OneToOneField(
        Booking, on_delete=models.PROTECT, related_name='order')
    order_number = models.CharField(max_length=12, unique=True, editable=False)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    stripe_pid = models.CharField(max_length=255, unique=True)
    paid_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-paid_on']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)