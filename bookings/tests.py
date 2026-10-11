from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import AvailabilitySlot, Booking
from readings.models import ReadingType
from .forms import BookingForm


def make_slot(days_ahead=3, hour=10):
    start = (timezone.now() + timedelta(days=days_ahead)).replace(
        hour=hour, minute=0, second=0, microsecond=0)
    return AvailabilitySlot.objects.create(
        start_time=start, end_time=start + timedelta(hours=1))


class AvailabilitySlotTests(TestCase):
    """Tests for the AvailabilitySlot model."""

    def setUp(self):
        self.start = timezone.now() + timedelta(days=7)

    def test_valid_future_slot_passes_validation(self):
        slot = AvailabilitySlot(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        slot.full_clean()  # raises an error if the slot is invalid

    def test_end_time_before_start_time_is_rejected(self):
        slot = AvailabilitySlot(
            start_time=self.start, end_time=self.start - timedelta(hours=1))
        with self.assertRaises(ValidationError):
            slot.full_clean()

    def test_slot_in_the_past_is_rejected(self):
        past = timezone.now() - timedelta(days=1)
        slot = AvailabilitySlot(start_time=past, end_time=past + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            slot.full_clean()

    def test_new_slot_is_not_booked(self):
        slot = AvailabilitySlot.objects.create(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        self.assertFalse(slot.is_booked)

    def test_slots_are_ordered_by_start_time(self):
        later = AvailabilitySlot.objects.create(
            start_time=self.start + timedelta(days=1),
            end_time=self.start + timedelta(days=1, hours=1))
        earlier = AvailabilitySlot.objects.create(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        self.assertEqual(list(AvailabilitySlot.objects.all()), [earlier, later])


class BookingTestSetup(TestCase):
    """Shared set-up: a client, a reading and a free future slot."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='client', password='testing123')
        self.reading = ReadingType.objects.create(
            name='Birth Chart', summary='Your natal chart',
            description='Full reading', price=85, duration_minutes=60)
        self.slot = make_slot()

    def booking_data(self, **changes):
        data = {
            'slot': self.slot.pk,
            'birth_date': '1980-06-17',
            'birth_time': '14:30',
            'birth_place': 'Chertsey',
            'question': '',
        }
        data.update(changes)
        return data


class BookingModelTests(BookingTestSetup):

    def create_booking(self, **changes):
        fields = {
            'user': self.user, 'reading_type': self.reading,
            'slot': self.slot, 'birth_date': date(1980, 6, 17),
            'birth_place': 'Chertsey',
        }
        fields.update(changes)
        return Booking.objects.create(**fields)

    def test_new_bookings_is_pending(self):
        self.assertEqual(self.create_booking().status, 'pending')

    def test_string_shows_user_and_reading(self):
        text = str(self.create_booking())
        self.assertIn('client', text)
        self.assertIn('Birth Chart', text)

    def test_slot_cannot_have_two_active_bookings(self):
        self.create_booking()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_booking()


    def test_cancelled_slot_can_be_booked_again(self):
        self.create_booking(status='cancelled')
        self.create_booking()
        self.assertEqual(Booking.objects.filter(slot='self'.slot).count(), 2)


class BookingFormTest(BookingTestSetup):
    
    def test_valid_form(self):
        self.assertTrue(BookingForm(data=self.booking_data()).is_valid())

    def test_birth_time_is_optional(self):
        form = BookingForm(data=self.booking_data(birth_time=''))
        self.assertTrue(form.is_valid())

    def test_future_birth_data_rejected(self):
        tomorrow = (data.today() + timedelta(days=1)).isoformat()
        form = BookingForm(data=self.booking_data(birth_date=tomorrow))
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)

    def test_booked_slot_rejected(self):
        self.slot.is_booked = True
        self.slot.save()
        form = BookingForm(data=self.booking_data())
        self.assertFalse(form.is_valid())
        self.assertIn('slot', form.errors)


class BookReadingViewTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('book_reading', args=[self.slug])

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={self.url}")

    def test_logged_in_user_sees_form(self):
        self.client.login(username='client', password='testing123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/book_reading.html')

    def test_booking_saved_and_slot_marked(self):
        self.client.login(username='client', password='testing123')
        self.client.post(self.url, self.booking_data())
        booking = Booking.objects.get()
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.reading_type, self.reading)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)

    def test_hidden_reading_cannot_be_booked(self):
        self.reading.is_active = False
        self.reading.save()
        self.client.login(username='client', password='testing123')
        self.assertEqual(self.client.get(self.url).status_code, 404)