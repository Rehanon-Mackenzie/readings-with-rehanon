from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'booking', 'amount', 'paid_on')
    readonly_fields = ('order_number', 'stripe_pid', 'paid_on')
