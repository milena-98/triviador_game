from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'player_one',
            'email': 'player@example.com',
            'nickname': 'MountainKnight',
            'password': 'example-password',
            'password_confirm': 'example-password',
        }

    def test_register_creates_user_and_profile(self):
        response = self.client.post('/api/auth/register/', self.user_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['username'], 'player_one')
        self.assertEqual(response.data['profile']['nickname'], 'MountainKnight')
        self.assertNotIn('password', response.data)

    def test_login_creates_session_and_me_works(self):
        self.client.post('/api/auth/register/', self.user_data, format='json')

        login_response = self.client.post(
            '/api/auth/login/',
            {'username': 'player_one', 'password': 'example-password'},
            format='json',
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertIn('sessionid', login_response.cookies)

        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data['username'], 'player_one')

    def test_profile_update_restricts_fields(self):
        self.client.post('/api/auth/register/', self.user_data, format='json')
        self.client.post('/api/auth/login/', {'username': 'player_one', 'password': 'example-password'}, format='json')

        response = self.client.patch(
            '/api/auth/me/',
            {'nickname': 'NewKnight', 'avatar_key': 'knight-3', 'email': 'new@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['nickname'], 'NewKnight')
        self.assertEqual(response.data['profile']['avatar_key'], 'knight-3')
        self.assertNotEqual(User.objects.get(username='player_one').email, 'new@example.com')

    def test_logout_ends_session(self):
        self.client.post('/api/auth/register/', self.user_data, format='json')
        self.client.post('/api/auth/login/', {'username': 'player_one', 'password': 'example-password'}, format='json')

        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, 204)

        me_response = self.client.get('/api/auth/me/')
        self.assertIn(me_response.status_code, [401, 403])

    def test_invalid_registration_returns_400(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'player_one',
                'email': 'player@example.com',
                'nickname': 'MountainKnight',
                'password': 'abc',
                'password_confirm': 'different',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)
