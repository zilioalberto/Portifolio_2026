import uuid
from django.db import models
from projects.models import Project

class BomSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="boms")
    version = models.PositiveIntegerField(default=1)
    generated_at = models.DateTimeField(auto_now_add=True)

class BomItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bom = models.ForeignKey(BomSuggestion, on_delete=models.CASCADE, related_name="items")

    category = models.CharField(max_length=40)
    manufacturer = models.CharField(max_length=40, default="SIEMENS")
    part_number = models.CharField(max_length=80, default="TBD")
    description = models.CharField(max_length=255)
    qty = models.PositiveIntegerField(default=1)

    meta = models.JSONField(default=dict, blank=True)

class ProjectAlert(models.Model):
    class Level(models.TextChoices):
        ERROR = "ERROR", "Error"
        WARN = "WARN", "Warn"
        INFO = "INFO", "Info"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alerts")

    level = models.CharField(max_length=10, choices=Level.choices)
    code = models.CharField(max_length=60)
    message = models.CharField(max_length=255)
    context = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)