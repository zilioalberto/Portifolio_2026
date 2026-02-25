import uuid
from django.db import models
from projects.models import Project

class ElectricalParams(models.Model):
    class PhaseSystem(models.TextChoices):
        ONE_PHASE = "1P", "1~"
        THREE_PHASE = "3P", "3~"

    class IccRange(models.TextChoices):
        KA_6 = "6", "6kA"
        KA_10 = "10", "10kA"
        KA_15 = "15", "15kA"
        KA_25 = "25", "25kA"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="electrical_params")

    voltage_v = models.PositiveIntegerField()
    frequency_hz = models.PositiveIntegerField(default=60)
    phase_system = models.CharField(max_length=2, choices=PhaseSystem.choices)
    has_neutral = models.BooleanField(default=False)

    icc_value_ka = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    icc_range_ka = models.CharField(max_length=2, choices=IccRange.choices, null=True, blank=True)

    control_voltage = models.CharField(max_length=16, default="24VDC")
    ambient_temp_c = models.PositiveIntegerField(default=35)
    ip_rating = models.CharField(max_length=10, default="IP54")
    standard = models.CharField(max_length=32, default="IEC_60204_1")

    has_drives_emc = models.BooleanField(default=False)  # flag sugerida no passo 1

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Load(models.Model):
    class LoadType(models.TextChoices):
        MOTOR = "MOTOR", "Motor"
        RESISTIVE = "RESISTIVE", "Resistive"
        AUX = "AUX", "Aux"
        DC24 = "DC24", "24Vdc"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="loads")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=10, choices=LoadType.choices)
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

class MotorLoad(models.Model):
    class DriveType(models.TextChoices):
        DOL = "DOL", "DOL"
        SOFTSTARTER = "SOFTSTARTER", "Softstarter"
        VFD = "VFD", "VFD"
        SERVO = "SERVO", "Servo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load = models.OneToOneField(Load, on_delete=models.CASCADE, related_name="motor")

    power_kw = models.DecimalField(max_digits=8, decimal_places=2)
    voltage_v = models.PositiveIntegerField()
    drive_type = models.CharField(max_length=16, choices=DriveType.choices)

    cosphi = models.DecimalField(max_digits=4, decimal_places=2, default=0.85)
    efficiency = models.DecimalField(max_digits=4, decimal_places=2, default=0.90)
    duty = models.CharField(max_length=10, default="S1")

    motor_cable_length_m = models.PositiveIntegerField(null=True, blank=True)

class ResistiveLoad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load = models.OneToOneField(Load, on_delete=models.CASCADE, related_name="resistive")

    power_kw = models.DecimalField(max_digits=8, decimal_places=2)
    voltage_v = models.PositiveIntegerField()

class AuxLoad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load = models.OneToOneField(Load, on_delete=models.CASCADE, related_name="aux")

    estimated_current_a = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_power_kw = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

class Dc24Load(models.Model):
    class Profile(models.TextChoices):
        PLC = "PLC", "PLC"
        IHM = "IHM", "IHM"
        SENSORS = "SENSORS", "Sensors"
        VALVES = "VALVES", "Valves"
        RELAYS = "RELAYS", "Relays"
        CUSTOM = "CUSTOM", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load = models.OneToOneField(Load, on_delete=models.CASCADE, related_name="dc24")

    profile = models.CharField(max_length=16, choices=Profile.choices, default=Profile.CUSTOM)
    current_a = models.DecimalField(max_digits=8, decimal_places=3, default=0.100)