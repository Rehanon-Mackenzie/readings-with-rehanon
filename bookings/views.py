from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone

from readings.models import ReadingType
from .forms import BookingForm, RescheduleForm
from .models import Booking


@login_required
def book_reading(request, slug):
    reading = get_object_or_404(ReadingType, slug=slug, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.reading_type = reading
                    booking.save()
                    booking.slot.is_booked = True
                    booking.slot.save()
            except IntegrityError:
                # Someone else booked this slot a moment earlier
                messages.error(request, 'Sorry that time has just been taken. Please choose another.')
                return redirect('book_reading', slug=reading.slug)
            messages.success(
                request, f'Your {reading.name} is held for {booking.slot} Please complete your payment to confirm it.')
            return redirect('checkout', booking_id=booking.pk)
        messages.error(request, 'Please check the form for errors.')
    else:
        form = BookingForm()

    return render(request, 'bookings/book_reading.html',
                  {'form': form, 'reading': reading})


@login_required
def my_bookings(request):
    now = timezone.now()
    bookings = request.user.bookings.select_related('reading_type', 'slot')

    upcoming = bookings.filter(
        slot__start_time__gt=now).exclude(status='cancelled')
    past = bookings.filter(
        Q(slot__start_time__lt=now) | Q(status='cancelled')
    ).order_by('-slot__start_time')

    return render(request, 'bookings/my_bookings.html', {'upcoming': upcoming, 'past': past})

@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if not booking.can_be_changed():
        messages.error(
            request,
            'Bookings can only be cancelled more than 48 hours before the reading.')
        return redirect('my_bookings')

    if request.method == 'POST':
        with transaction.atomic():
            booking.status = 'cancelled'
            booking.save()
            booking.slot.is_booked = False
            booking.slot.save()
        messages.success(
            request,
            f'Your {booking.reading_type.name} on {booking.slot} has been cancelled.')
        return redirect('my_bookings')

    return render(request, 'bookings/cancel_booking.html', {'booking': booking})


@login_required
def reschedule_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if not booking.can_be_changed():
        messages.error(
            request,
            'Bookings can only be moved more than 48 hours before the reading.')
        return redirect('my_bookings')

    old_slot = booking.slot

    if request.method == 'POST':
        form = RescheduleForm(request.POST, instance=booking)
        if form.is_valid():
            try:
                with transaction.atomic():
                    old_slot.is_booked = False
                    old_slot.save()
                    booking = form.save()
                    booking.slot.is_booked = True
                    booking.slot.save()
            except IntegrityError:
                messages.error(request, 'Sorry that time has just been taken. Please choose another.')
                return redirect('reschedule_booking', pk=booking.pk)
            messages.success(
                request, f'Your {booking.reading_type.name} has been moved to {booking.slot}.')
            return redirect('my_bookings')
    else:
        form = RescheduleForm(instance=booking)

    return render(request, 'bookings/reschedule_booking.html',
                  {'form': form, 'booking': booking})
