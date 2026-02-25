from django.urls import path
from .views import GenerateBomView, LatestBomView, ProjectAlertsView

urlpatterns = [
    path("projects/<uuid:project_id>/generate-bom/", GenerateBomView.as_view()),
    path("projects/<uuid:project_id>/bom/", LatestBomView.as_view()),
    path("projects/<uuid:project_id>/alerts/", ProjectAlertsView.as_view()),
]