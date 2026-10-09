from django.contrib import admin

from .models import AvailabilitySlot


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_booked')
    list_filter = ('is_booked',)
