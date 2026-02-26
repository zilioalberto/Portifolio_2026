from rest_framework import serializers
from .models import Project

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "panel_type", "wizard_step", "created_at", "updated_at"]
        read_only_fields = ["id", "wizard_step", "created_at", "updated_at"]

class ProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "panel_type", "wizard_step", "created_by", "created_at", "updated_at"]
        read_only_fields = fields