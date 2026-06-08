from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class SmokeTest(TestCase):
    
    def test_modules_list_redirects_to_login(self):
        url = reverse("modules:entry_list")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={url}",
            fetch_redirect_response=False
        )
        
    def test_modules_list_loads_for_logged_in_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        self.client.force_login(user)
        
        url = reverse("modules:entry_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)