from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from poll_app.core.models import Choice, Poll, Question


class PollsTestCase(TestCase):
    def setUp(self):
        # Создание пользователей
        self.user = User.objects.create_user(username="user", password="1234")
        self.admin = User.objects.create_superuser(
            username="admin", password="1234", email="admin@example.com"
        )

        # Создание опроса
        self.poll = Poll.objects.create(
            title="Test Poll", description="Some desc", created_by=self.admin
        )
        self.question = Question.objects.create(
            poll=self.poll, text="Your favorite color?"
        )
        self.choice1 = Choice.objects.create(question=self.question, choice_text="Red")
        self.choice2 = Choice.objects.create(question=self.question, choice_text="Blue")

        self.client = Client()

        self.user.is_staff = True
        self.user.save()

    def test_index_view(self):
        response = self.client.get(reverse("poll_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.title)

    def test_poll_detail_requires_login(self):
        response = self.client.get(reverse("poll_detail", args=[self.poll.pk]))
        self.assertEqual(response.status_code, 302)  # редирект на login

        self.client.login(username="user", password="1234")
        response = self.client.get(reverse("poll_detail", args=[self.poll.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.text)

    def test_poll_results(self):
        self.client.login(username="admin", password="1234")
        response = self.client.get(reverse("poll_results", args=[self.poll.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.choice1.choice_text)

    def test_vote(self):
        self.client.login(username="user", password="1234")
        vote_url = reverse("poll_vote", args=[self.poll.pk])
        response = self.client.post(
            vote_url, {f"question_{self.question.pk}": self.choice1.pk}
        )
        self.assertRedirects(response, reverse("poll_results", args=[self.poll.pk]))

    def test_statistics_access(self):
        self.client.login(username="user", password="1234")
        response = self.client.get(reverse("poll_statistics"))
        self.assertEqual(response.status_code, 403)

        self.client.login(username="admin", password="1234")
        response = self.client.get(reverse("poll_statistics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Итоговая статистика")
