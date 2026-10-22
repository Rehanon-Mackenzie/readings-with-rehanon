from datetime import date, timedelta

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
        slot = AvailabilitySlot(
            start_time=past, end_time=past + timedelta(hours=1))
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
        self.assertEqual(list(AvailabilitySlot.objects.all()),
                         [earlier, later])


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

    def make_booking(self, user, slot, **changes):
        fields = {
            'user': user, 'reading_type': self.reading, 'slot': slot,
            'birth_date': date(1980, 6, 17), 'birth_place': 'Glasgow',
        }
        fields.update(changes)
        return Booking.objects.create(**fields)

    def login(self):
        self.client.login(username='client', password='testing123')


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
        self.assertEqual(Booking.objects.filter(slot=self.slot).count(), 2)

    def test_cancelling_booking_frees_slot(self):
        booking = self.create_booking()
        booking.status = 'cancelled'
        booking.save()
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)

    def test_active_booking_marks_slot_booked(self):
        self.create_booking()
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)

    def test_editing_old_cancelled_booking_keeps_slot_booked(self):
        old = self.create_booking(status='cancelled')
        self.create_booking()  # a new active booking in the same slot
        old.question = 'Updated'
        old.save()
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)


class BookingFormTest(BookingTestSetup):

    def test_valid_form(self):
        self.assertTrue(BookingForm(data=self.booking_data(),
                        reading=self.reading).is_valid())

    def test_birth_time_is_optional(self):
        form = BookingForm(data=self.booking_data(
            birth_time=''), reading=self.reading)
        self.assertTrue(form.is_valid())

    def test_future_birth_data_rejected(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        form = BookingForm(data=self.booking_data(
            birth_date=tomorrow), reading=self.reading)
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)

    def test_booked_slot_rejected(self):
        self.slot.is_booked = True
        self.slot.save()
        form = BookingForm(data=self.booking_data(), reading=self.reading)
        self.assertFalse(form.is_valid())
        self.assertIn('slot', form.errors)

    def make_short_slot(self, minutes=45):
        start = (timezone.now() + timedelta(days=4)).replace(
            hour=10, minute=0, second=0, microsecond=0)
        return AvailabilitySlot.objects.create(
            start_time=start,
            end_time=start + timedelta(minutes=minutes))

    def test_slot_too_short_for_reading_rejected(self):
        short = self.make_short_slot(45)
        form = BookingForm(data=self.booking_data(
            slot=short.pk), reading=self.reading)
        self.assertFalse(form.is_valid())
        self.assertIn('slot', form.errors)

    def test_slot_exactly_long_enough_accepted(self):
        # self.slot is 60 minutes and the reading is 60 minutes
        form = BookingForm(data=self.booking_data(), reading=self.reading)
        self.assertTrue(form.is_valid())


class BookReadingViewTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('book_reading', args=[self.reading.slug])

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


class MyBookingsViewTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('my_bookings')
        self.other_user = User.objects.create_user(
            username='gemini', password='password123')

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={self.url}")

    def test_uses_my_bookings_template(self):
        self.login()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'bookings/my_bookings.html')

    def test_shows_own_upcoming_bookings(self):
        booking = self.make_booking(self.user, self.slot)
        self.login()
        response = self.client.get(self.url)
        self.assertIn(booking, response.context['upcoming'])
        self.assertContains(response, 'Birth Chart')

    def test_does_not_show_other_users_bookings(self):
        other_booking = self.make_booking(self.other_user, self.slot)
        self.login()
        response = self.client.get(self.url)
        self.assertNotIn(other_booking, response.context['upcoming'])
        self.assertNotIn(other_booking, response.context['past'])

    def test_past_booking_listed_as_past(self):
        old = self.make_booking(self.user, make_slot(days_ahead=-3))
        self.login()
        response = self.client.get(self.url)
        self.assertIn(old, response.context['past'])
        self.assertNotIn(old, response.context['upcoming'])

    def test_cancelled_booking_not_upcoming(self):
        cancelled = self.make_booking(self.user, self.slot, status='cancelled')
        self.login()
        response = self.client.get(self.url)
        self.assertNotIn(cancelled, response.context['upcoming'])
        self.assertIn(cancelled, response.context['past'])

    def test_message_when_no_bookings(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, "You haven't booked any readings yet")


class CancelBookingTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.booking = self.make_booking(self.user, self.slot)
        self.slot.is_booked = True
        self.slot.save()
        self.url = reverse('cancel_booking', args=[self.booking.pk])

    # the 48-hour cancellation (model)
    def test_can_change_more_than_48_hours_ahead(self):
        self.assertTrue(self.booking.can_be_changed())

    def test_cannot_change_within_48_hours(self):
        soon = self.make_booking(self.user, make_slot(days_ahead=1))
        self.assertFalse(soon.can_be_changed())

    def test_cancelled_booking_cannot_be_changed(self):
        self.booking.status = 'cancelled'
        self.assertFalse(self.booking.can_be_changed())

    # cancel page (view)
    def test_get_shows_confirmation_and_changes_nothing(self):
        self.login()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'bookings/cancel_booking.html')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')

    def test_owner_can_cancel_and_slot_is_freed(self):
        self.login()
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('my_bookings'))
        self.booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertFalse(self.slot.is_booked)

    def test_other_user_cannot_cancel(self):
        User.objects.create_user(username='other', password='password123')
        self.client.login(username='other', password='password123')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')

    def test_cannot_cancel_within_48_hours(self):
        soon = self.make_booking(self.user, make_slot(days_ahead=1))
        self.login()
        self.client.post(reverse('cancel_booking', args=[soon.pk]))
        soon.refresh_from_db()
        self.assertEqual(soon.status, 'pending')


class RescheduledBookingTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.booking = self.make_booking(self.user, self.slot)
        self.slot.is_booked = True
        self.slot.save()
        self.new_slot = make_slot(days_ahead=5)
        self.url = reverse('reschedule_booking', args=[self.booking.pk])

    def test_gets_shows_reschedule_page(self):
        self.login()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'bookings/reschedule_booking.html')

    def test_owner_can_move_to_new_slot(self):
        self.login()
        response = self.client.post(self.url, {'slot': self.new_slot.pk})
        self.assertRedirects(response, reverse('my_bookings'))
        self.booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.new_slot.refresh_from_db()
        self.assertEqual(self.booking.slot, self.new_slot)
        self.assertFalse(self.slot.is_booked)  # old slot released
        self.assertTrue(self.new_slot.is_booked)  # new slot booked

    def test_other_user_cannot_reschedule(self):
        User.objects.create_user(username='other', password='password123')
        self.client.login(username='other', password='password123')
        response = self.client.post(self.url, {'slot': self.new_slot.pk})
        self.assertEqual(response.status_code, 404)

    def test_cannot_reschedule_within_48_hours(self):
        soon_slot = make_slot(days_ahead=1)
        soon = self.make_booking(self.user, soon_slot)
        self.login
        self.client.post(reverse('reschedule_booking', args=[soon.pk]),
                         {'slot': self.new_slot.pk})
        soon.refresh_from_db()
        self.assertEqual(soon.slot, soon_slot)

    def test_cannot_moved_to_booked_slot(self):
        self.new_slot.is_booked = True
        self.new_slot.save()
        self.login()
        self.client.post(self.url, {'slot': self.new_slot.pk})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.slot, self.slot)

    def test_cannot_move_to_slot_too_short(self):
        start = (timezone.now() + timedelta(days=6)).replace(
            hour=10, minute=0, second=0, microsecond=0)
        short = AvailabilitySlot.objects.create(
            start_time=start, end_time=start + timedelta(minutes=45))
        self.login()
        self.client.post(self.url, {'slot': short.pk})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.slot, self.slot)


class SlotManagementTests(BookingTestSetup):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@testing.com', password='testing123')
        self.list_url = reverse('manage_slots')
        self.add_url = reverse('add_slot')

    def admin_login(self):
        self.client.login(username='admin', password='testing123')

    def slot_data(self, days_ahead=7, hours_long=1):
        start = (timezone.localtime() + timedelta(days=days_ahead)).replace(
            hour=14, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=hours_long)
        return {'start_time': start.strftime('%Y-%m-%dT%H:%M'),
                'end_time': end.strftime('%Y-%m-%dT%H:%M')}

    # Who can get in
    def test_anonymous_sent_to_login(self):
        response = self.client.get(self.list_url)
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={self.list_url}")

    def test_client_cannot_manage_slots(self):
        self.login()
        response = self.client.get(self.list_url)
        self.assertRedirects(response, reverse('home'))

    def test_admin_sees_slot_list(self):
        self.admin_login()
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, 'bookings/manage_slots.html')
        self.assertIn(self.slot, response.context['slots'])

    # Adding
    def test_admin_can_add_slot(self):
        self.admin_login
        self.client.post(self.add_url, self.slot_data(hours_long=-1))
        self.assertEqual(AvailabilitySlot.objects.count(), 1)

    def test_end_before_start_rejected(self):
        self.admin_login()
        self.client.post(self.add_url, self.slot_data(days_ahead=-2))
        self.assertEqual(AvailabilitySlot.objects.count(), 1)

    # Deleting
    def test_can_admin_delete_free_slot(self):
        self.admin_login()
        url = reverse('delete_slot', args=[self.slot.pk])
        self.client.post(url)
        self.assertFalse(AvailabilitySlot.objects.filter(
            pk=self.slot.pk).exists())

    def test_delete_button_hidden_for_slot_with_cancelled_booking(self):
        self.make_booking(self.user, self.slot, status='cancelled')
        self.admin_login()
        response = self.client.get(self.list_url)
        self.assertNotContains(
            response, reverse('delete_slot', args=[self.slot.pk]))
