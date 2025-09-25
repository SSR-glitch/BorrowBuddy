from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from .models import User

class UserVerificationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_verification_flow(self):
        # Simulate user signup
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123',
        })
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        # Check that the user is created and is inactive
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)

        # Simulate email verification
        verification_url = reverse('verify_email', args=[user.verification_token])
        response = self.client.get(verification_url)

        # Check that the user is now active and verified
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        
        # Check that the user is logged in after verification
        self.assertEqual(int(response.wsgi_request.user.id), user.id)
