from django.shortcuts import render

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from projects.models import Project
from .models import ElectricalParams, Load, MotorLoad, ResistiveLoad, AuxLoad, Dc24Load
from .serializers import (
    ElectricalParamsSerializer,
    LoadCreateSerializer,
    LoadListSerializer
)

class ProjectStep1View(APIView):
    permission_classes = [permissions.AllowAny]  # MVP

    def put(self, request, project_id):
        project = Project.objects.get(id=project_id)

        instance = getattr(project, "electrical_params", None)
        serializer = ElectricalParamsSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(project=project)
        # avança wizard
        project.wizard_step = Project.WizardStep.STEP2
        project.save(update_fields=["wizard_step"])

        return Response({"message": "Step1 salvo com sucesso.", "electrical_params": ElectricalParamsSerializer(obj).data})

class ProjectLoadsView(APIView):
    permission_classes = [permissions.AllowAny]  # MVP

    def get(self, request, project_id):
        project = Project.objects.get(id=project_id)
        loads = project.loads.all().order_by("created_at")
        return Response(LoadListSerializer(loads, many=True).data)

    def post(self, request, project_id):
        project = Project.objects.get(id=project_id)

        s = LoadCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        base = Load.objects.create(
            project=project,
            name=s.validated_data["name"],
            type=s.validated_data["type"],
            quantity=s.validated_data.get("quantity", 1),
        )

        t = base.type
        if t == Load.LoadType.MOTOR:
            MotorLoad.objects.create(load=base, **s.validated_data["motor"])
        elif t == Load.LoadType.RESISTIVE:
            ResistiveLoad.objects.create(load=base, **s.validated_data["resistive"])
        elif t == Load.LoadType.AUX:
            AuxLoad.objects.create(load=base, **s.validated_data["aux"])
        elif t == Load.LoadType.DC24:
            Dc24Load.objects.create(load=base, **s.validated_data["dc24"])

        # mantém STEP2
        if project.wizard_step == Project.WizardStep.STEP1:
            project.wizard_step = Project.WizardStep.STEP2
            project.save(update_fields=["wizard_step"])

        return Response({"message": "Carga adicionada.", "load": LoadListSerializer(base).data}, status=status.HTTP_201_CREATED)