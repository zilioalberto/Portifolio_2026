import math
from decimal import Decimal

from projects.models import Project
from specs.models import ElectricalParams, Load
from bom.models import BomSuggestion, BomItem, ProjectAlert

def _motor_current_a(power_kw: Decimal, voltage_v: int, cosphi: Decimal, efficiency: Decimal, three_phase: bool) -> Decimal:
    # I ≈ P / (sqrt(3)*V*η*cosφ) for 3~
    # I ≈ P / (V*η*cosφ) for 1~
    p_w = power_kw * Decimal(1000)
    denom = Decimal(voltage_v) * cosphi * efficiency
    if three_phase:
        denom *= Decimal(str(math.sqrt(3)))
    if denom == 0:
        return Decimal("0")
    return p_w / denom

def _resistive_current_a(power_kw: Decimal, voltage_v: int, three_phase: bool) -> Decimal:
    # Resistiva (aprox): I ≈ P / (sqrt(3)*V) for 3~ ; I ≈ P / V for 1~
    p_w = power_kw * Decimal(1000)
    denom = Decimal(voltage_v)
    if three_phase:
        denom *= Decimal(str(math.sqrt(3)))
    if denom == 0:
        return Decimal("0")
    return p_w / denom

def generate_bom_v1(project: Project) -> BomSuggestion:
    # limpa alertas anteriores (simples para MVP)
    ProjectAlert.objects.filter(project=project).delete()

    ep: ElectricalParams = getattr(project, "electrical_params", None)
    if not ep:
        ProjectAlert.objects.create(
            project=project, level=ProjectAlert.Level.ERROR,
            code="STEP1_MISSING",
            message="Parâmetros elétricos (Step 1) não foram preenchidos.",
            context={}
        )
        raise ValueError("Step1 missing")

    # valida Icc
    icc_ka = ep.icc_value_ka or (Decimal(ep.icc_range_ka) if ep.icc_range_ka else None)
    if icc_ka is None:
        ProjectAlert.objects.create(
            project=project, level=ProjectAlert.Level.ERROR,
            code="ICC_MISSING",
            message="Icc não informado: informe o valor (kA) ou selecione uma faixa.",
            context={}
        )
        raise ValueError("Icc missing")

    three_phase = ep.phase_system == ElectricalParams.PhaseSystem.THREE_PHASE

    loads = project.loads.all()
    total_i = Decimal("0")
    total_dc24 = Decimal("0")

    # correntes estimadas
    for l in loads:
        qty = Decimal(str(l.quantity))

        if l.type == Load.LoadType.MOTOR and hasattr(l, "motor"):
            m = l.motor
            i = _motor_current_a(m.power_kw, m.voltage_v, m.cosphi, m.efficiency, three_phase) * qty
            total_i += i

        elif l.type == Load.LoadType.RESISTIVE and hasattr(l, "resistive"):
            r = l.resistive
            i = _resistive_current_a(r.power_kw, r.voltage_v, three_phase) * qty
            total_i += i

        elif l.type == Load.LoadType.AUX and hasattr(l, "aux"):
            a = l.aux
            if a.estimated_current_a is not None:
                total_i += Decimal(a.estimated_current_a) * qty
            elif a.estimated_power_kw is not None:
                total_i += _resistive_current_a(a.estimated_power_kw, ep.voltage_v, three_phase) * qty
            else:
                ProjectAlert.objects.create(
                    project=project, level=ProjectAlert.Level.WARN,
                    code="AUX_UNDERSPEC",
                    message=f"Carga auxiliar '{l.name}' sem corrente/potência estimada. Não entrou no cálculo.",
                    context={"load_id": str(l.id)}
                )

        elif l.type == Load.LoadType.DC24 and hasattr(l, "dc24"):
            d = l.dc24
            total_dc24 += Decimal(d.current_a) * qty

    # fator de folga/disponibilidade
    itotal = total_i
    itotal_with_margin = itotal * Decimal("1.20")

    # polos
    poles = "4P" if (three_phase and ep.has_neutral) else ("3P" if three_phase else "1P")

    # Icu regra (MVP): Icu >= Icc
    # Aqui vamos sugerir um "Icu nominal" como texto, sem catálogo real ainda.
    icu_required = f">= {icc_ka} kA"

    # cria BOM
    bom = BomSuggestion.objects.create(project=project, version=1)

    # Disjuntor geral (placeholder)
    BomItem.objects.create(
        bom=bom,
        category="MAIN_BREAKER",
        description="Disjuntor Geral (sugerido)",
        qty=1,
        manufacturer="SIEMENS",
        part_number="TBD",
        meta={
            "In_estimated_a": str(itotal_with_margin.quantize(Decimal("0.01"))),
            "Icu_required": icu_required,
            "poles": poles,
        },
    )

    # Seccionamento (MVP: assumimos que existe no painel se usuário não informou)
    ProjectAlert.objects.create(
        project=project, level=ProjectAlert.Level.INFO,
        code="MAIN_ISOLATION_ASSUMED",
        message="Seccionamento geral considerado no painel como padrão seguro (ajustável no futuro).",
        context={}
    )
    BomItem.objects.create(
        bom=bom,
        category="MAIN_ISOLATOR",
        description="Seccionadora geral / manopla porta (sugerido)",
        qty=1,
        manufacturer="SIEMENS",
        part_number="TBD",
        meta={"poles": poles},
    )

    # Ramais motores (placeholder por carga)
    for l in loads:
        if l.type == Load.LoadType.MOTOR and hasattr(l, "motor"):
            m = l.motor

            # alertas EMC
            if m.drive_type in ("VFD", "SERVO") and not ep.has_drives_emc:
                ProjectAlert.objects.create(
                    project=project, level=ProjectAlert.Level.WARN,
                    code="EMC_RECOMMENDED",
                    message=f"Carga '{l.name}' tem {m.drive_type}. Recomenda-se marcar 'tem drives/EMC' para habilitar itens EMC.",
                    context={"load_id": str(l.id)}
                )

            BomItem.objects.create(
                bom=bom,
                category="MOTOR_BRANCH",
                description=f"Ramo motor '{l.name}' ({m.drive_type}) - conjunto proteção/comando (sugerido)",
                qty=int(l.quantity),
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={
                    "drive_type": m.drive_type,
                    "power_kw": str(m.power_kw),
                    "voltage_v": m.voltage_v,
                },
            )

    # Fonte 24Vdc (se houver)
    if total_dc24 > 0:
        psu_current = (total_dc24 * Decimal("1.30")).quantize(Decimal("0.001"))
        BomItem.objects.create(
            bom=bom,
            category="PSU_24VDC",
            description="Fonte 24Vdc (sugerida)",
            qty=1,
            manufacturer="SIEMENS",
            part_number="TBD",
            meta={"required_current_a": str(psu_current)},
        )

        # alerta de supressores se houver válvulas/relés
        has_valves_relays = any(
            (hasattr(l, "dc24") and l.dc24.profile in ("VALVES", "RELAYS"))
            for l in loads if l.type == Load.LoadType.DC24
        )
        if has_valves_relays:
            ProjectAlert.objects.create(
                project=project, level=ProjectAlert.Level.INFO,
                code="SUPPRESSORS_RECOMMENDED",
                message="Detectadas válvulas/relés em 24Vdc. Recomenda-se uso de supressores (diodo/RC) conforme aplicável.",
                context={}
            )

    # atualiza wizard step
    project.wizard_step = Project.WizardStep.STEP3
    project.save(update_fields=["wizard_step"])

    return bom