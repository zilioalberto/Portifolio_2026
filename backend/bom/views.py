from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from projects.models import Project
from .models import BomSuggestion, ProjectAlert
from .serializers import BomSuggestionSerializer, ProjectAlertSerializer
from .services.dimensioning import generate_bom_v1

class GenerateBomView(APIView):
    permission_classes = [permissions.AllowAny]  # MVP

    def post(self, request, project_id):
        project = Project.objects.get(id=project_id)
        try:
            bom = generate_bom_v1(project)
        except ValueError:
            # retorna alertas como feedback
            alerts = ProjectAlert.objects.filter(project=project).order_by("-created_at")
            return Response(
                {"message": "Falha ao gerar BOM.", "alerts": ProjectAlertSerializer(alerts, many=True).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        alerts = ProjectAlert.objects.filter(project=project).order_by("-created_at")
        return Response(
            {
                "message": "BOM gerada com sucesso.",
                "bom": BomSuggestionSerializer(bom).data,
                "alerts": ProjectAlertSerializer(alerts, many=True).data,
            },
            status=status.HTTP_201_CREATED
        )

class LatestBomView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, project_id):
        project = Project.objects.get(id=project_id)
        bom = BomSuggestion.objects.filter(project=project).order_by("-generated_at").first()
        if not bom:
            return Response({"message": "Nenhuma BOM gerada ainda."}, status=status.HTTP_404_NOT_FOUND)
        return Response(BomSuggestionSerializer(bom).data)

class ProjectAlertsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, project_id):
        project = Project.objects.get(id=project_id)
        alerts = ProjectAlert.objects.filter(project=project).order_by("-created_at")
        return Response(ProjectAlertSerializer(alerts, many=True).data)