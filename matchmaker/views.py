import json
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import MatchForm
from .models import MatchRequest, LastfmUser
from .tasks import run_match


def home(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = MatchForm(request.POST)
        if form.is_valid():
            username_a = form.cleaned_data["username_a"]
            username_b = form.cleaned_data["username_b"]
            user_a, _ = LastfmUser.objects.get_or_create(username=username_a)
            user_b, _ = LastfmUser.objects.get_or_create(username=username_b)
            if username_a == username_b:
                match = MatchRequest.objects.create(
                    user_a=user_a,
                    user_b=user_b,
                    status="READY",
                    result={
                        "final_score": 100.0,
                        "scores": {"3month": 1.0, "12month": 1.0, "overall": 1.0},
                        "overlap": [],
                        "recs_for_a": [],
                        "recs_for_b": [],
                        "warning": "Comparing a user to themselves; automatically 100%.",
                    },
                )
            else:
                match = MatchRequest.objects.create(user_a=user_a, user_b=user_b, status="PENDING")
                try:
                    run_match(str(match.uuid))
                except Exception as exc:
                    match.status = "FAILED"
                    match.error_message = str(exc)
                    match.save(update_fields=["status", "error_message", "updated_at"])
            return redirect(reverse("match_detail", args=[match.uuid]))
    else:
        form = MatchForm()
    return render(request, "matchmaker/home.html", {"form": form})


def match_detail(request: HttpRequest, match_id: str) -> HttpResponse:
    match = get_object_or_404(MatchRequest, uuid=match_id)
    if match.status == "PENDING":
        return render(request, "matchmaker/match_loading.html", {"match": match})
    if match.status == "FAILED":
        return render(request, "matchmaker/match_detail.html", {"match": match, "error": match.error_message})

    return render(
        request,
        "matchmaker/match_detail.html",
        {
            "match": match,
            "result": match.result or {},
            "user_a": match.user_a,
            "user_b": match.user_b,
        },
    )


def match_status(request: HttpRequest, match_id: str) -> JsonResponse:
    try:
        match = MatchRequest.objects.get(uuid=match_id)
    except MatchRequest.DoesNotExist:
        raise Http404

    data = {"status": match.status}
    if match.status == "READY":
        data["redirect"] = reverse("match_detail", args=[match.uuid])
    if match.status == "FAILED":
        data["error"] = match.error_message
    return JsonResponse(data)
