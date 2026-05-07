from django.urls import path
from .views import positions_list, position_candidates

app_name = "elections"

urlpatterns = [
 
    path("positions/", positions_list, name="positions_list"),
    path("positions/<int:position_id>/", position_candidates, name="position_candidates")
]



