from rest_framework import serializers
from .models import BomSuggestion, BomItem, ProjectAlert

class BomItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomItem
        fields = ["id", "category", "manufacturer", "part_number", "description", "qty", "meta"]

class BomSuggestionSerializer(serializers.ModelSerializer):
    items = BomItemSerializer(many=True, read_only=True)

    class Meta:
        model = BomSuggestion
        fields = ["id", "version", "generated_at", "items"]

class ProjectAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAlert
        fields = ["id", "level", "code", "message", "context", "created_at"]