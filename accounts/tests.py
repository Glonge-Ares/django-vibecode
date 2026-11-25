from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm

User = get_user_model()


class RegisterTests(TestCase):
    def test_register_page_renders(self):
        resp = self.client.get(reverse("register"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "name=\"email\"")
        self.assertContains(resp, "Create an account")

    def test_successful_registration_stores_email_and_logs_in(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "newbie",
                "email": "Newbie@Example.COM",
                "password1": "s3cure-Passw0rd!",
                "password2": "s3cure-Passw0rd!",
            },
        )
        self.assertRedirects(resp, reverse("exam-list"))
        user = User.objects.get(username="newbie")
        self.assertEqual(user.email, "newbie@example.com")
        self.assertTrue(user.check_password("s3cure-Passw0rd!"))
        self.assertIn("_auth_user_id", self.client.session)
        resp = self.client.get(reverse("exam-list"))
        self.assertContains(resp, "Log out (newbie)")

    def test_duplicate_email_rejected(self):
        User.objects.create_user("taken", password="x", email="dup@example.com")
        resp = self.client.post(
            reverse("register"),
            {
                "username": "someone",
                "email": "DUP@example.com",
                "password1": "s3cure-Passw0rd!",
                "password2": "s3cure-Passw0rd!",
            },
        )
        self.assertContains(resp, "already exists")
        self.assertFalse(User.objects.filter(username="someone").exists())

    def test_invalid_email_rejected(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "badmail",
                "email": "not-an-email",
                "password1": "s3cure-Passw0rd!",
                "password2": "s3cure-Passw0rd!",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="badmail").exists())

    def test_mismatched_passwords_rejected(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "typo",
                "email": "typo@example.com",
                "password1": "s3cure-Passw0rd!",
                "password2": "s3cure-Passw0rd!!",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="typo").exists())

    def test_common_password_rejected_by_validators(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "lazy",
                "email": "lazy@example.com",
                "password1": "password123",
                "password2": "password123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="lazy").exists())

    def test_authenticated_user_redirected(self):
        User.objects.create_user("inuse", password="pass12345")
        self.client.login(username="inuse", password="pass12345")
        resp = self.client.get(reverse("register"))
        self.assertRedirects(resp, reverse("exam-list"))

    def test_login_page_links_to_register(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, reverse("register"))
