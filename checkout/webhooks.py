import stripe

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bookings.models import Booking
from .payments import confirm_booking_payment


@require_POST
@csrf_exempt
def webhook(request):
    """Receive payment events from Stripe."""
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META.get('HTTP_STRIPE_SIGNATURE', ''),
            settings.STRIPE_WH_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        # Not a genuine message from Stripe
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        try:
            booking = Booking.objects.get(pk=intent['metadata']['booking_id'])
        except (KeyError, Booking.DoesNotExist):
            # A payment that isn't one of our bookings
            return HttpResponse(status=200)
        confirm_booking_payment(booking, intent['id'], intent['amount'])

    return HttpResponse(status=200)
