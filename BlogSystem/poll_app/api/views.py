from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from poll_app.core.models import Choice, Poll, Question, Vote


def poll_list(request):
    polls = (
        Poll.objects.filter(is_active=True)
        .prefetch_related("questions")
        .annotate(num_questions=Count("questions"))
    )
    query = request.GET.get("q")
    if query:
        polls = polls.filter(title__icontains=query)
    return render(request, "polls/index.html", {"polls": polls})


@login_required
def poll_detail(request, poll_id):
    poll = get_object_or_404(
        Poll.objects.prefetch_related(
            Prefetch("questions", queryset=Question.objects.prefetch_related("choices"))
        ),
        pk=poll_id,
    )
    return render(request, "polls/detail.html", {"poll": poll})


@login_required
def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    for question in poll.questions.all():
        choice_id = request.POST.get(f"question_{question.id}")
        if choice_id:
            choice = get_object_or_404(Choice, pk=choice_id)
            Vote.objects.update_or_create(
                user=request.user,
                choice__question=question,
                defaults={"choice": choice},
            )
    return redirect("poll_results", poll_id=poll.id)


def poll_results(request, poll_id):
    poll = get_object_or_404(
        Poll.objects.prefetch_related(
            Prefetch("questions", queryset=Question.objects.prefetch_related("choices"))
        ),
        pk=poll_id,
    )
    return render(request, "polls/results.html", {"poll": poll})


@login_required
def poll_statistics(request):
    if not request.user.is_superuser:
        raise PermissionDenied()
    polls = Poll.objects.prefetch_related(
        Prefetch("questions", queryset=Question.objects.prefetch_related("choices"))
    )

    stats = []
    for poll in polls:
        poll_data = {"poll": poll, "questions": []}
        for question in poll.questions.all():
            choices_stats = []
            for choice in question.choices.all():
                vote_count = Vote.objects.filter(choice=choice).count()
                choices_stats.append({"choice": choice, "votes": vote_count})
            poll_data["questions"].append(
                {"question": question, "choices": choices_stats}
            )
        stats.append(poll_data)

    return render(request, "polls/statistics.html", {"stats": stats})
