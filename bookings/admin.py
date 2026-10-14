from django.contrib import admin

from .models import AvailabilitySlot, Booking


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_booked')
    list_filter = ('is_booked',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'reading_type', 'slot', 'status')
    list_filter = ('status',)
