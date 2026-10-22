from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string

from decimal import Decimal

from .models import Order

import logging

logger = logging.getLogger(__name__)


def send_confirmation_email(order):
    """Email the client a summary of their confirmed booking.
    Any email problem is logged, never allowed to break the payment."""
    try:
        context = {'order': order, 'booking': order.booking}
        subject = render_to_string(
            'checkout/emails/confirmation_subject.txt', context).strip()
        body = render_to_string(
            'checkout/emails/confirmation_body.txt', context)
        send_mail(subject, body, None, [order.booking.user.email])
    except Exception:
        logger.exception(
            'Confirmation email failed for order %s', order.order_number)


def confirm_booking_payment(booking, payment_intent_id, amount_pence):
    """
    Record a successful payment and confirm the booking. The success page and
    the webhook can both call it without creating a second order.
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
        if created:
            send_confirmation_email(order)
    return order
