from rest_framework import serializers
from .models import ElectricalParams, Load, MotorLoad, ResistiveLoad, AuxLoad, Dc24Load
from projects.models import Project

class ElectricalParamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricalParams
        fields = [
            "voltage_v", "frequency_hz", "phase_system", "has_neutral",
            "icc_value_ka", "icc_range_ka",
            "control_voltage", "ambient_temp_c", "ip_rating",
            "standard", "has_drives_emc",
        ]

    def validate(self, attrs):
        icc_value = attrs.get("icc_value_ka")
        icc_range = attrs.get("icc_range_ka")

        if icc_value is None and not icc_range:
            raise serializers.ValidationError(
                {"icc_range_ka": "Icc não informado. Se não tiver o valor, selecione uma faixa (6/10/15/25kA)."}
            )
        return attrs

class LoadBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Load
        fields = ["id", "project", "name", "type", "quantity", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"project": {"write_only": True}}

class MotorLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotorLoad
        fields = ["power_kw", "voltage_v", "drive_type", "cosphi", "efficiency", "duty", "motor_cable_length_m"]

class ResistiveLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResistiveLoad
        fields = ["power_kw", "voltage_v"]

class AuxLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuxLoad
        fields = ["estimated_current_a", "estimated_power_kw"]

class Dc24LoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dc24Load
        fields = ["profile", "current_a"]

class LoadCreateSerializer(serializers.Serializer):
    """
    Payload:
    {
      "name": "...",
      "type": "MOTOR|RESISTIVE|AUX|DC24",
      "quantity": 1,
      "motor": {...} OR "resistive": {...} OR "aux": {...} OR "dc24": {...}
    }
    """
    name = serializers.CharField(max_length=120)
    type = serializers.ChoiceField(choices=Load.LoadType.choices)
    quantity = serializers.IntegerField(min_value=1, default=1)

    motor = MotorLoadSerializer(required=False)
    resistive = ResistiveLoadSerializer(required=False)
    aux = AuxLoadSerializer(required=False)
    dc24 = Dc24LoadSerializer(required=False)

    def validate(self, attrs):
        t = attrs["type"]
        required_map = {
            Load.LoadType.MOTOR: "motor",
            Load.LoadType.RESISTIVE: "resistive",
            Load.LoadType.AUX: "aux",
            Load.LoadType.DC24: "dc24",
        }
        required_key = required_map[t]
        if required_key not in attrs:
            raise serializers.ValidationError({required_key: f"Campos obrigatórios para carga {t}."})
        return attrs

class LoadListSerializer(serializers.ModelSerializer):
    motor = MotorLoadSerializer(read_only=True)
    resistive = ResistiveLoadSerializer(read_only=True)
    aux = AuxLoadSerializer(read_only=True)
    dc24 = Dc24LoadSerializer(read_only=True)

    class Meta:
        model = Load
        fields = ["id", "name", "type", "quantity", "created_at", "motor", "resistive", "aux", "dc24"]
        read_only_fields = fields