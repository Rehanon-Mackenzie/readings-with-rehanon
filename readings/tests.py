from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from decimal import Decimal

from .models import ReadingType


class ReadingTypeModelTests(TestCase):
    """Tests for the ReadingType model."""

    def test_string_representation_is_the_name(self):
        reading = ReadingType(name='Birth Chart Reading')
        self.assertEqual(str(reading), 'Birth Chart Reading')

class ReadingViewTests(TestCase):
    """Tests for the readings list and detail pages."""

    def setUp(self):
        self.reading = ReadingType.objects.create(
            name='Birth Chart Reading',
            slug='birth-chart-reading',
            summary='A full reading of your natal chart.',
            description='A detailed look at your birth chart.',
            price=Decimal('85.00'),
            duration_minutes=60,
        )
        self.hidden_reading = ReadingType.objects.create(
            name='Retired Reading',
            slug='retired-reading',
            summary='No longer offered.',
            description='No longer offered.',
            price=Decimal('50.00'),
            duration_minutes=30,
            is_active=False,
        )

    def test_list_page_loads_with_correct_template(self):
        response = self.client.get(reverse('reading_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'readings/reading_list.html')

    def test_list_page_shows_active_readings_only(self):
        response = self.client.get(reverse('reading_list'))
        self.assertContains(response, 'Birth Chart Reading')
        self.assertNotContains(response, 'Retired Reading')

    def test_detail_page_shows_the_reading(self):
        response = self.client.get(reverse('reading_detail', args=['birth-chart-reading']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A detailed look at your birth chart.')

    def test_detail_page_returns_404_for_inactive_reading(self):
        response = self.client.get(reverse('reading_detail', args=['retired-reading']))
        self.assertEqual(response.status_code, 404)

    def test_detail_page_returns_404_for_unknown_reading(self):
        response = self.client.get(reverse('reading_detail', args=['does-not-exist']))
        self.assertEqual(response.status_code, 404)


class ReadingSlugTests(TestCase):
    """The slug is created automatically from the name."""

    def test_slug_is_generated_from_name(self):
        reading = ReadingType.objects.create(
            name='Tarot Three Card Spread',
            summary='Summary',
            description='Description',
            price=Decimal('30.00'),
            duration_minutes=30,
        )
        self.assertEqual(reading.slug, 'tarot-three-card-spread')


class ReadingManagementTests(TestCase):
    """Only the superuser can add, edit, and delete readings."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='testing123')
        self.client_user = User.objects.create_user(
            username='client', password='client123')
        self.reading = ReadingType.objects.create(
            name='Birth Chart Reading',
            summary='A full reading of your natal chart.',
            description='A detailed look at your birth chart.',
            price=Decimal('85.00'),
            duration_minutes=60,
        )
        self.valid_data = {
            'name': 'Solar Return Chart',
            'summary': 'Your year ahead.',
            'description': 'A look at the year from your birthday.',
            'price': '40.00',
            'duration_minutes': 45,
            'is_active': True,
        }

    # Access control
    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('add_reading'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_client_cannot_open_add_page(self):
        self.client.login(username='client', password='client123')
        response = self.client.get(reverse('add_reading'))
        self.assertRedirects(response, reverse('home'))

    def test_client_cannot_delete_a_reading(self):
        self.client.login(username='client', password='client123')
        self.client.post(reverse('delete_reading', args=[self.reading.slug]))
        self.assertTrue(ReadingType.objects.filter(pk=self.reading.pk).exists())

    # Create
    def test_admin_can_add_a_reading(self):
        self.client.login(username='admin', password='testing123')
        response = self.client.post(reverse('add_reading'), self.valid_data)
        new_reading = ReadingType.objects.get(name='Solar Return Chart')
        self.assertRedirects(response, new_reading.get_absolute_url())

    def test_negative_price_is_rejected(self):
        self.client.login(username='admin', password='testing123')
        data = {**self.valid_data, 'price': '-5.00'}
        response = self.client.post(reverse('add_reading'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReadingType.objects.filter(name='Solar Return Chart').exists())

    # Update
    def test_admin_can_edit_a_reading(self):
        self.client.login(username='admin', password='testing123')
        data = {**self.valid_data, 'name': 'Birth Chart Reading', 'price': '90.00'}
        self.client.post(reverse('edit_reading', args=[self.reading.slug]), data)
        self.reading.refresh_from_db()
        self.assertEqual(self.reading.price, Decimal('90.00'))

    # Delete
    def test_admin_can_delete_a_reading(self):
        self.client.login(username='admin', password='testing123')
        response = self.client.post(reverse('delete_reading', args=[self.reading.slug]))
        self.assertRedirects(response, reverse('reading_list'))
        self.assertFalse(ReadingType.objects.filter(pk=self.reading.pk).exists())

    # Hidden readings
    def test_admin_sees_hidden_readings_on_list(self):
        self.reading.is_active = False
        self.reading.save()
        self.client.login(username='admin', password='testing123')
        response = self.client.get(reverse('reading_list'))
        self.assertContains(response, 'Birth Chart Reading')
