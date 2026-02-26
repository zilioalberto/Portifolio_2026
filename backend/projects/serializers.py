from rest_framework import serializers
from .models import Project

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "panel_type", "demand_factor", "wizard_step", "created_by", "created_at", "updated_at"]
        read_only_fields = fields
        
    def validate_demand_factor(self, value):
        # permite 0.10 a 1.00 (ajuste se quiser)
        if value < 0.10 or value > 1.00:
            raise serializers.ValidationError("demand_factor deve estar entre 0.10 e 1.00.")
        return value


