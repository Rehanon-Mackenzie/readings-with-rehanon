from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core import mail

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from bookings.models import AvailabilitySlot, Booking
from readings.models import ReadingType
from .models import Order
from .payments import confirm_booking_payment


class CheckoutTestSetup(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='client', email='client@testing.com', password='testing123')
        reading = ReadingType.objects.create(
            name='Birth Chart', summary='Your natal chart',
            description='Full reading', price=85, duration_minutes=60,)
        start = timezone.now() + timedelta(days=3)
        slot = AvailabilitySlot.objects.create(
            start_time=start, end_time=start + timedelta(hours=1))
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


class CheckoutViewTests(CheckoutTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('checkout', args=[self.booking.pk])

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={self.url}")

    @patch('checkout.views.stripe.PaymentIntent.create')
    def test_checkout_page_shows_payment_form(self, mock_create):
        mock_create.return_value = MagicMock(client_secret='pi_test_secret')
        self.client.login(username='client', password='testing123')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'checkout/checkout.html')
        self.assertContains(response, 'pi_test_secret')
        # £85 must be sent to Stripe as 8500 pence
        self.assertEqual(mock_create.call_args.kwargs['amount'], 8500)

    @patch('checkout.views.stripe.PaymentIntent.create')
    def test_other_users_gets_404(self, mock_create):
        User.objects.create_user(username='other', password='password123')
        self.client.login(username='other', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        mock_create.assert_not_called()

    @patch('checkout.views.stripe.PaymentIntent.create')
    def test_confirmed_booking_cannot_be_paid_again(self, mock_create):
        self.booking.status = 'confirmed'
        self.booking.save()
        self.client.login(username='client', password='testing123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class CheckoutSuccessTests(CheckoutTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('checkout_success', args=[self.booking.pk])
        self.client.login(username='client', password='testing123')

    def fake_intent(self, status='succeeded', booking_id=None):
        return MagicMock(
            id='pi_test_1', status=status, amount=8500,
            metadata={'booking_id': str(booking_id or self.booking.pk)})

    @patch('checkout.views.stripe.PaymentIntent.retrieve')
    def test_successful_payment_confirms_booking(self, mock_retrieve):
        mock_retrieve.return_value = self.fake_intent()
        response = self.client.get(self.url, {'payment_intent': 'pi_test_1'})
        self.assertTemplateUsed(response, 'checkout/checkout_success.html')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertTrue(Order.objects.filter(booking=self.booking).exists())

    @patch('checkout.views.stripe.PaymentIntent.retrieve')
    def test_unfinished_payment_does_not_confirm(self, mock_retrieve):
        mock_retrieve.return_value = self.fake_intent(
            status='requires_payment_method')
        response = self.client.get(self.url, {'payment_intent': 'pi_test_1'})
        self.assertRedirects(
            response, reverse('checkout', args=[self.booking.pk]),
            fetch_redirect_response=False)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')
        self.assertEqual(Order.objects.count(), 0)

    @patch('checkout.views.stripe.PaymentIntent.retrieve')
    def test_payment_for_another_booking_is_rejected(self, mock_retrieve):
        mock_retrieve.return_value = self.fake_intent(booking_id=999)
        self.client.get(self.url, {'payment_intent': 'pi_test_1'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')


class ConfirmationEmailTests(CheckoutTestSetup):

    def test_email_sent_when_booking_confirmed(self):
        order = confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['client@testing.com'])
        self.assertIn(order.order_number, mail.outbox[0].body)

    def test_email_sent_only_once(self):
        confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        confirm_booking_payment(self.booking, 'pi_test_1', 8500)
        self.assertEqual(len(mail.outbox), 1)


class WebhookTests(CheckoutTestSetup):

    def setUp(self):
        super().setUp()
        self.url = reverse('webhook')

    def stripe_event(self, booking_id):
        return {
            'type': 'payment_intent.succeeded',
            'data': {'object': {
                'id': 'pi_test_1', 'amount': 8500,
                'metadata': {'booking_id': str(booking_id)},
            }}
        }

    def post_event(self):
        return self.client.post(
            self.url, data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature')

    @patch('checkout.webhooks.stripe.Webhook.construct_event')
    def test_payment_succeeded_confirms_booking(self, mock_construct):
        mock_construct.return_value = self.stripe_event(self.booking.pk)
        response = self.post_event()
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertEqual(Order.objects.count(), 1)

    @patch('checkout.webhooks.stripe.Webhook.construct_event')
    def test_invalid_signature_rejected(self, mock_construct):
        mock_construct.side_effect = ValueError('Invalid payload')
        response = self.post_event()
        self.assertEqual(response.status_code, 400)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')

    @patch('checkout.webhooks.stripe.Webhook.construct_event')
    def test_unknown_booking_is_ignored(self, mock_construct):
        mock_construct.return_value = self.stripe_event(999)
        response = self.post_event()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
