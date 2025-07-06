import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poll_app.settings")
django.setup()

import random

from django.contrib.auth.models import User

from poll_app.core.models import Choice, Poll, Question


def seed_polls():
    user = User.objects.filter(is_staff=True).first() or User.objects.first()
    if not user:
        print("❗ Нет пользователей для создания опроса")
        return

    titles = [
        "Как вы оцениваете нашу платформу?",
        "Ваши предпочтения в еде?",
        "Какой язык программирования лучше?",
    ]

    for title in random.sample(titles, k=2):
        poll = Poll.objects.create(
            title=title,
            description="Автосгенерированный опрос",
            created_by=user,
            is_active=True,
        )

        for i in range(1, 4):
            question = Question.objects.create(poll=poll, text=f"Вопрос {i} — {title}")
            for j in range(1, 5):
                Choice.objects.create(question=question, choice_text=f"Вариант {j}")


if __name__ == "__main__":
    seed_polls()
