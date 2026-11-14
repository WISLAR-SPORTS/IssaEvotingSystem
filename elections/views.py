from django.shortcuts import render
from .models import Position, Election
from voting.models import Vote
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q


from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone


from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from students.models import StudentRecord  # Adjust import if StudentRecord is in another app



@login_required
def positions_list(request):
    user = request.user
    now = timezone.now()

    if user.role == "super_admin":
        elections = Election.objects.all()
    else:
        elections = Election.objects.filter(
            institution_id=user.institution_id
        )

    upcoming_elections = []
    active_elections = []
    ended_elections = []

    for election in elections:
        if election.start_time > now:
            upcoming_elections.append(election)
        elif election.start_time <= now <= election.end_time:
            active_elections.append(election)
        else:
            ended_elections.append(election)

    positions = Position.objects.filter(
        election__in=active_elections
    )

        
    if user.role != "super_admin":
        positions = positions.filter(
            institution_id=user.institution_id
        )

        student_record = (
            StudentRecord.objects
            .filter(user=user)
            .select_related("department", "branch")
            .first()
        )

        allowed_positions = Q(is_central=True)

        if student_record:
            # Department-specific positions
            if student_record.department_id:
                allowed_positions |= Q(
                    department_id=student_record.department_id,
                    is_central=False,
                )

        # Branch-specific positions
        if student_record.branch_id:
            allowed_positions |= Q(
                branch_id=student_record.branch_id,
                department__isnull=True,
                is_central=False,
            )

    positions = positions.filter(
        allowed_positions
    ).distinct()

    return render(request, "elections/positions.html", {
        "positions": positions,
        "upcoming_elections": upcoming_elections,
        "ended_elections": ended_elections,
        "no_active_elections": not active_elections,
    })


from django.shortcuts import render, get_object_or_404
from .models import Position, Candidate
from voting.models import Vote
from django.utils import timezone


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils import timezone
from django.db.models import Q

from .models import Position, Candidate
from voting.models import Vote


@login_required
def position_candidates(request, position_id):
    user = request.user

    # Super admins can access positions across institutions.
    # Other users must belong to an institution.
    is_super_admin = user.role == "super_admin"

    if is_super_admin:
        position = get_object_or_404(
            Position,
            id=position_id
        )
    else:
        institution = getattr(user, "institution", None)

        if institution is None:
            raise Http404("Position not found.")

        # Enforce institution isolation.
        position = get_object_or_404(
            Position,
            id=position_id,
            institution=institution
        )

    election = position.election
    now = timezone.now()

    # Election has not started.
    if now < election.start_time:
        return render(request, "elections/not_started.html", {
            "election": election
        })

    # Election has ended.
    if now > election.end_time:
        return render(request, "elections/ended.html", {
            "election": election
        })

    # Retrieve candidates for this position and its institution.
    candidates = Candidate.objects.filter(
        position=position,
        institution=position.institution
    ).select_related("user")

    # Apply student-specific restrictions to ordinary users.
    if not is_super_admin:
        if not position.is_central:
            candidates = candidates.filter(
                branch=user.branch
            )

        department = getattr(user, "department", None)

        if department:
            candidates = candidates.filter(
                Q(department=department) |
                Q(department__isnull=True)
            )

    # Check the current user's voting status.
    has_voted = Vote.objects.filter(
        voter=user,
        position=position
    ).exists()

    user_vote = (
        Vote.objects.filter(
            voter=user,
            position=position
        )
        .select_related("candidate")
        .first()
    )

    return render(request, "elections/candidates.html", {
        "position": position,
        "candidates": candidates,
        "has_voted": has_voted,
        "user_vote": user_vote,
    })
from django.shortcuts import render
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from elections.models import Election, Position, Candidate
from voting.models import Vote


@staff_member_required
def live_results_view(request):
    institution = getattr(request.user, "institution", None)
    now = timezone.now()

    elections = Election.objects.none()
    results = []

    if institution:
        elections = Election.objects.filter(
            institution=institution,
            start_time__lte=now,
            end_time__gte=now,
        ).order_by("-start_time")

        for election in elections:
            positions = Position.objects.filter(
                election=election,
                institution=institution,
            ).select_related(
                "branch",
                "department",
            )

            for position in positions:
                # Get candidates for this position.
                candidates = list(
                    Candidate.objects.filter(
                        position=position,
                        institution=institution,
                    ).select_related(
                        "user",
                        "branch",
                        "department",
                        "position",
                    )
                )

                # Start with votes belonging to this institution,
                # election, and position.
                vote_query = Vote.objects.filter(
                    institution=institution,
                    position=position,
                    candidate__institution=institution,
                    candidate__position=position,
                )

                # Match votes to the position's scope.
                if position.is_central:
                    # Institution-wide position.
                    pass

                elif position.department_id:
                    vote_query = vote_query.filter(
                        department_id=position.department_id,
                        candidate__department_id=position.department_id,
                    )

                elif position.branch_id:
                    vote_query = vote_query.filter(
                        branch_id=position.branch_id,
                        candidate__branch_id=position.branch_id,
                    )

                # Count votes for each candidate in one query.
                vote_counts = {
                    row["candidate_id"]: row["votes"]
                    for row in vote_query.values(
                        "candidate_id"
                    ).annotate(
                        votes=Count("id")
                    )
                }

                # Attach vote totals to each candidate.
                for candidate in candidates:
                    candidate.votes = vote_counts.get(
                        candidate.pk, 0
                    )

                # Total votes cast for this position and scope.
                total_votes = sum(
                    candidate.votes for candidate in candidates
                )

                # Calculate each candidate's percentage.
                for candidate in candidates:
                    candidate.percentage = (
                        round(
                            candidate.votes * 100 / total_votes,
                            2,
                        )
                        if total_votes
                        else 0
                    )

                # Sort from highest votes to lowest.
                candidates.sort(
                    key=lambda candidate: candidate.votes,
                    reverse=True,
                )

                # Assign competition ranks: 1, 1, 3 for a tie.
                previous_votes = None
                current_rank = 0

                for index, candidate in enumerate(
                    candidates, start=1
                ):
                    if candidate.votes != previous_votes:
                        current_rank = index

                    candidate.rank = current_rank
                    previous_votes = candidate.votes

                results.append({
                    "election": election,
                    "position": position,
                    "candidates": candidates,
                    "total_votes": total_votes,
                })

    context = {
        "title": "Live Election Results",
        "institution": institution,
        "elections": elections,
        "results": results,
    }

    return render(
        request,
        "admin/elections/live_results.html",
        context,
    )
