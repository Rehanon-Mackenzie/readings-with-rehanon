from django.test import TestCase
from django.urls import reverse

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
