from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import date, timedelta
from decimal import Decimal

from bookings.models import AvailabilitySlot, Booking
from readings.models import ReadingType
from .models import Order
from .payments import confirm_booking_payment


class CheckoutTestSetup(TestCase):

    def setUp(self):
        self.user - User.objects.create_user(
            username='client', password='testing123')
        reading = ReadingType.objects.create(
            name='Birth Chart', summary='Your natal chart',
            description='Full reading', price=85, duration_minutes=60,)
        start = timezone.now() + timedelta(days=3)
        slot = AvailabilitySlot.objects.create(
            star_time=start, end_time=start + timedelta(hours=1))
        self.booking = Booking.objects.create(
            user=self.user, reading_type=reading, slot=slot,
            birth_date=date(1980, 6, 17), birth_place='Brighton')


class OrderTests(CheckoutTestSetup):

    def test_order_number_generated(self):
        order = Order.objects.create(
            booking=self.booking, amount=Decimal('85.00'), stripe_pid='pi_test_1')
        self.assertEqual(len(order.order_number), 12)

    def test_confirm_payment_creates_order_and_confirms_booking(self):
        order = confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertEqual(order.amount, Decimal('85.00'))
        self.assertEqual(order.stripe_pid, 'pi_test_1')

    def test_confirm_payment_twice_makes_only_one_order(self):
        confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        self.assertEqual(Order.objects.count(), 1)
