from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectCreateSerializer, ProjectDetailSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]  # MVP (depois troca pra JWT)

    queryset = Project.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return ProjectDetailSerializer
        return ProjectCreateSerializer

    def perform_create(self, serializer):
        # MVP: sem auth, mas precisa preencher created_by.
        # Se não houver user autenticado, usa o primeiro user, ou cria um depois.
        request_user = getattr(self.request, "user", None)
        if request_user and request_user.is_authenticated:
            serializer.save(created_by=request_user)
            return

        # fallback MVP: pega o primeiro usuário do banco
        from accounts.models import User
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(username="admin", password="admin", role=User.Role.ADMIN)
        serializer.save(created_by=user)