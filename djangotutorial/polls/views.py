from django.db.models import F, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from polls.tests import create_question

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self) -> QuerySet[Question]:
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self) -> QuerySet[Question]:
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def index(request: HttpRequest) -> HttpResponse:
    latest_question_list: QuerySet[Question] = Question.objects.order_by("-pub_date")[
        :5
    ]
    template = generic.get_template("polls/index.html")
    context: dict[str, QuerySet[Question]] = {
        "latest_question_list": latest_question_list
    }
    return HttpResponse(template.render(context, request))


def detail(request: HttpRequest, question_id: int) -> HttpResponse:
    question: Question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})


def results(request: HttpRequest, question_id: int) -> HttpResponse:
    question: Question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})


def vote(request: HttpRequest, question_id: int) -> HttpResponseRedirect | HttpResponse:
    question: Question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class QuestionDetailViewTests(TestCase):
    def test_future_question(self) -> None:
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question: Question = create_question(
            question_text="Future question.", days=5
        )
        url: str = reverse("polls:detail", args=(future_question.id,))
        response: HttpResponse = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self) -> None:
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question: Question = create_question(
            question_text="Past Question.", days=-5
        )
        url: str = reverse("polls:detail", args=(past_question.id,))
        response: HttpResponse = self.client.get(url)
        self.assertContains(response, past_question.question_text)
