from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class HomePageTests(TestCase):
    """Tests for the home page view."""

    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/index.html')

    def test_anonymous_user_sees_login_and_register_links(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Log in')
        self.assertContains(response, 'Register')
        self.assertNotContains(response, 'Log out')

    def test_logged_in_user_sees_logout_link(self):
        User.objects.create_user(username='tester', password='testing123')
        self.client.login(username='tester', password='testing123')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Log out')
        self.assertNotContains(response, 'Register')
