import uuid
from django.conf import settings
from django.db import models
from decimal import Decimal

class Project(models.Model):
    class PanelType(models.TextChoices):
        AUTOMATION = "AUTOMATION", "Automation"
        DISTRIBUTION = "DISTRIBUTION", "Distribution"

    class WizardStep(models.TextChoices):
        STEP1 = "STEP1", "Step 1"
        STEP2 = "STEP2", "Step 2"
        STEP3 = "STEP3", "Step 3"
        DONE = "DONE", "Done"
        
          
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    panel_type = models.CharField(max_length=16, choices=PanelType.choices)
    wizard_step = models.CharField(max_length=8, choices=WizardStep.choices, default=WizardStep.STEP1)
    
    
    demand_factor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.00"),
        help_text="Fator de demanda/simultaneidade (ex.: 0.70).",
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.panel_type})"