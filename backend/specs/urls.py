from django.urls import path
from .views import ProjectStep1View, ProjectLoadsView

urlpatterns = [
    path("projects/<uuid:project_id>/step1/", ProjectStep1View.as_view()),
    path("projects/<uuid:project_id>/loads/", ProjectLoadsView.as_view()),
]