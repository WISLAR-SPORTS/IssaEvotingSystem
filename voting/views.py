from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.views.decorators.http import require_POST
from .models import Vote
from elections.models import Candidate
from elections.models import Position
from django.contrib.auth.decorators import login_required

from django.db import IntegrityError
@login_required
@require_POST
def cast_vote(request, candidate_id):
    user = request.user

    candidate = get_object_or_404(
        Candidate,
        id=candidate_id,
        institution=user.institution
    )

    position = candidate.position

    
    if Vote.objects.filter(voter=user, position=position).exists():
        messages.error(request, "You have already voted for this position.")
        return redirect("elections:position_candidates", position_id=position.id)

    # 🔒 branch protection
    if not position.is_central and candidate.branch != user.branch:
        messages.error(request, "Invalid candidate for your branch.")
        return redirect("elections:position_candidates", position_id=position.id)

    try:
        vote = Vote(
            voter=user,
            candidate=candidate,
            position=position,
            institution=user.institution,
            branch=user.branch
        )

        vote.full_clean()  # ✅ VERY IMPORTANT
        vote.save()

        messages.success(request, "Vote cast successfully!")

    except IntegrityError:
        messages.error(request, "Duplicate vote detected.")

    except Exception as e:
        messages.error(request, str(e))

    return redirect("elections:position_candidates", position_id=position.id)

from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.shortcuts import render
from django.http import JsonResponse

from django.db.models import Prefetch, Count

@login_required
def election_results(request):
    user = request.user
    results_data = []

    # Prefetch candidates with annotated vote counts
    positions = Position.objects.filter(institution=user.institution).prefetch_related(
        Prefetch(
            "candidate_set",
            queryset=Candidate.objects.annotate(total_votes=Count("vote"))
        )
    )

    for position in positions:
        # Use pre-fetched candidates
        candidates = position.candidate_set.all()

        if not position.is_central:
            candidates = candidates.filter(branch=user.branch)

        candidates = list(candidates)

        # 🔥 total votes across all candidates
        total_votes = sum(c.total_votes for c in candidates)

        winner = None
        max_votes = 0

        # 🚫 CASE 1: NO VOTES YET
        if total_votes == 0:
            for c in candidates:
                c.vote_percent = 0
                c.is_winner = False

        # ✅ CASE 2: VOTES EXIST
        else:
            for c in candidates:
                c.vote_percent = round((c.total_votes / total_votes) * 100, 1)

                if c.total_votes > max_votes:
                    max_votes = c.total_votes
                    winner = c

            for c in candidates:
                c.is_winner = (winner is not None and c.id == winner.id)

        results_data.append({
            "position": position,
            "candidates": candidates
        })

    return render(request, "elections/results.html", {
        "results_data": results_data
    })


@login_required
def live_results_api(request):
    user = request.user

    # Prefetch candidates with annotated vote counts
    positions = Position.objects.filter(
        institution=user.institution
    ).prefetch_related(
        Prefetch(
            "candidate_set",
            queryset=Candidate.objects.annotate(total_votes=Count("vote"))
        )
    )

    data = []

    for position in positions:
        # Use pre-fetched candidates
        candidates = position.candidate_set.all()

        if not position.is_central:
            candidates = candidates.filter(branch=user.branch)

        candidates = list(candidates)

        total_votes = sum(c.total_votes for c in candidates) or 1

        enriched = [
            {
                "id": c.id,
                "username": c.user.username,
                "total_votes": c.total_votes,
                "vote_percent": round((c.total_votes / total_votes) * 100, 1)
            }
            for c in candidates
        ]

        data.append({
            "position": position.name,
            "candidates": enriched
        })

    return JsonResponse({"data": data})