from django.urls import path
from .views import cast_vote, election_results, live_results_api



app_name = "voting"

urlpatterns = [
    path("vote/<int:candidate_id>/", cast_vote, name="cast_vote"),
    path("results/", election_results, name="election_results"),
    path("api/live-results/", live_results_api, name="live_results_api")
]