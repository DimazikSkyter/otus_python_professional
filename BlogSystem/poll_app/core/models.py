from django.contrib.auth.models import User
from django.db import models


class Poll(models.Model):
    title: models.CharField = models.CharField(max_length=200)
    description: models.TextField = models.TextField(blank=True)
    created_by: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    is_active: models.BooleanField = models.BooleanField(default=True)


class Question(models.Model):
    poll: models.ForeignKey = models.ForeignKey(
        Poll, related_name="questions", on_delete=models.PROTECT
    )
    text: models.TextField = models.TextField(blank=False)
    pud_date: models.DateTimeField = models.DateTimeField(
        "date published", auto_now_add=True
    )

    def __str__(self):
        return self.text


class Choice(models.Model):
    question: models.ForeignKey = models.ForeignKey(
        Question, related_name="choices", on_delete=models.CASCADE
    )
    choice_text: models.CharField = models.CharField(max_length=200)
    votes: models.IntegerField = models.IntegerField(default=0)


class Vote(models.Model):
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    choice: models.ForeignKey = models.ForeignKey(Choice, on_delete=models.CASCADE)
    voted_at: models.DateTimeField = models.DateTimeField(
        "Time voted", auto_now_add=True
    )
