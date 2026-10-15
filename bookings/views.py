from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone

from readings.models import ReadingType
from .forms import BookingForm


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
                request, f'Your {reading.name} is held for {booking.slot}.')
            return redirect('reading_detail', slug=reading.slug)
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
