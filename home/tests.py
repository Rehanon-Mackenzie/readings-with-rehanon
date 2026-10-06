from django.test import TestCase
from django.urls import reverse

class HomePageTests(TestCase):
    """Tests for the home page view."""


    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


    def test_home_page_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/index.html')
