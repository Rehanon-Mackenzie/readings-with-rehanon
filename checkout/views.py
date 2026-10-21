import stripe

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings

from bookings.models import Booking
from .payments import confirm_booking_payment


@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(
        Booking, pk=booking_id, user=request.user, status='pending')
    amount = int(booking.reading_type.price * 100)  # Stripe uses pence

    stripe.api_key = settings.STRIPE_SECRET_KEY
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=settings.STRIPE_CURRENCY,
        metadata={'booking_id': booking.pk, 'username': request.user.username},
    )

    return_url = request.build_absolute_uri(
        reverse('checkout_success', args=[booking.pk]))

    return render(request, 'checkout/checkout.html', {
        'booking': booking,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': intent.client_secret,
        'return_url': return_url,
    })


@login_required
def checkout_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    # Already paid (e.g. the page was refreshed): just show the confirmation
    if booking.status == 'confirmed':
        return render(request, 'checkout/checkout_success.html',
                      {'booking': booking, 'order': booking.order})

    intent_id = request.GET.get('payment_intent')
    if intent_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.retrieve(intent_id)
        paid = intent.status == 'succeeded'
        right_booking = intent.metadata['booking_id'] == str(booking.pk)
        if paid and right_booking:
            order = confirm_booking_payment(booking, intent.id, intent.amount)
            return render(request, 'checkout/checkout_success.html',
                          {'booking': booking, 'order': order})

    messages.error(
        request, "We couldn't confirm your payment. Please try again.")
    return redirect('checkout', booking_id=booking.pk)
