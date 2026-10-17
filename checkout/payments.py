from django.db import transaction

from decimal import Decimal

from .models import Order


def confirm_booking_payment(booking, payment_intent_id, amount_pence):
    """
    Record a successful payment and confirm the booking. The success page and the
    webhook can both call it without creating a second order.
    """

    with transaction.atomic():
        order, created = Order.objects.get_or_create(
            booking=booking,
            defaults={
                'amount': Decimal(amount_pence) / 100,
                'stripe_pid': payment_intent_id,
            },
        )
        if booking.status != 'confirmed':
            booking.status = 'confirmed'
            booking.save()
    return order