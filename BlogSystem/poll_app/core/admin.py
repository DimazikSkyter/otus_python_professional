from django.contrib import admin

from .models import Choice, Poll, Question, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class PollAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ("title", "created_by", "created_at")


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]


admin.site.register(Poll, PollAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Vote)
