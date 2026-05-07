from django.shortcuts import render
from .models import Position, Election
from voting.models import Vote
from django.contrib.auth.decorators import login_required
from django.utils import timezone


@login_required
def positions_list(request):
    user = request.user
    now = timezone.now()

    # Multi-tenant safe elections
    if user.role == "super_admin":
        elections = Election.objects.all()
    else:
        elections = Election.objects.filter(
            institution=user.institution
        )

    upcoming_elections = []
    active_elections = []
    ended_elections = []

    # ✅ FIXED LOGIC (do NOT rely on election.status)
    for election in elections:

        # 🟡 UPCOMING
        if election.start_time > now:
            upcoming_elections.append(election)
            continue

        # 🟢 ACTIVE
        if election.start_time <= now <= election.end_time:
            active_elections.append(election)
            continue

        # 🔴 ENDED
        ended_elections.append(election)

    # Only active positions
    if user.role == "super_admin":
        positions = Position.objects.filter(
            election__in=active_elections
        )
    else:
        positions = Position.objects.filter(
            institution=user.institution,
            election__in=active_elections
        )

    no_active_elections = len(active_elections) == 0

    return render(request, "elections/positions.html", {
        "positions": positions,
        "upcoming_elections": upcoming_elections,
        "ended_elections": ended_elections,
        "no_active_elections": no_active_elections,
    })
from django.shortcuts import render, get_object_or_404
from .models import Position, Candidate

def position_candidates(request, position_id):
    user = request.user

    position = get_object_or_404(
        Position,
        id=position_id,
        institution=user.institution
    )

    election = position.election
    now = timezone.now()

    # 🚫 Not started yet
    if now < election.start_time:
        return render(request, "elections/not_started.html", {
            "election": election
        })

    # 🚫 Already ended
    if now > election.end_time:
        return render(request, "elections/ended.html", {
            "election": election
        })

    # ✅ Only runs if election is ACTIVE (current time is within range)
    candidates = Candidate.objects.filter(
        position=position,
        institution=user.institution
    )

    if not position.is_central:
        candidates = candidates.filter(branch=user.branch)

    has_voted = Vote.objects.filter(
        voter=user,
        position=position
    ).exists()

    user_vote = Vote.objects.filter(
        voter=user,
        position=position
    ).select_related("candidate").first()

    return render(request, "elections/candidates.html", {
        "position": position,
        "candidates": candidates,
        "has_voted": has_voted,
        "user_vote": user_vote
    })