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

 # --- Dimensionamento: aplicar demanda + folga ---
    itotal_raw = total_i
    demand_factor = Decimal(str(project.demand_factor or Decimal("1.00")))
    itotal_demanda = (itotal_raw * demand_factor)
    itotal_dimensionamento = (itotal_demanda * Decimal("1.20"))  # folga 20%

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
            "In_estimated_a": str(itotal_dimensionamento.quantize(Decimal("0.01"))),
            "Icu_required": icu_required,
            "poles": poles,
            "demand_factor": str(demand_factor),
            "itotal_raw_a": str(itotal_raw.quantize(Decimal("0.01"))),
            "itotal_demanda_a": str(itotal_demanda.quantize(Decimal("0.01"))),
        },
    )

    # Seccionamento (MVP: assumimos que existe no painel se usuário não informou)
   
    # --- Seccionamento do painel ---
    if not ep.has_main_isolation:
        ProjectAlert.objects.create(
            project=project, level=ProjectAlert.Level.INFO,
            code="MAIN_ISOLATION_NONE",
            message="Projeto definido sem seccionamento (seccionadora) no painel.",
            context={}
    )
    else:
        if ep.main_isolation_type == "DISCONNECTOR":
            BomItem.objects.create(
            bom=bom,
            category="MAIN_ISOLATOR",
            description="Seccionadora geral (sugerida)",
            qty=1,
            manufacturer="SIEMENS",
            part_number="TBD",
            meta={"poles": poles},
        )
        elif ep.main_isolation_type == "MCCB":
            BomItem.objects.create(
            bom=bom,
            category="MAIN_MCCB",
            description="Disjuntor Caixa Moldada (MCCB) como seccionamento (sugerido)",
            qty=1,
            manufacturer="SIEMENS",
            part_number="TBD",
            meta={
                "poles": poles,
                "In_estimated_a": str(itotal_dimensionamento.quantize(Decimal("0.01"))),
                "Icu_required": icu_required,
            },
        )

        if ep.mccb_has_external_handle:
            BomItem.objects.create(
                bom=bom,
                category="MCCB_EXTERNAL_HANDLE",
                description="Manopla externa para MCCB (sugerida)",
                qty=1,
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={"model": ep.mccb_external_handle_model or "TBD"},
            )
        else:
            ProjectAlert.objects.create(
            project=project, level=ProjectAlert.Level.WARN,
            code="MAIN_ISOLATION_TYPE_MISSING",
            message="Seccionamento no painel habilitado, mas tipo não definido.",
            context={}
        )


    # Ramais motores (placeholder por carga)
    for l in loads:
        if l.type == Load.LoadType.MOTOR and hasattr(l, "motor"):
            m = l.motor

            # calcula corrente estimada do motor (por unidade)
        motor_i_unit = _motor_current_a(m.power_kw, m.voltage_v, m.cosphi, m.efficiency, three_phase)
        motor_i_total = (motor_i_unit * Decimal(str(l.quantity))).quantize(Decimal("0.01"))

        # alertas EMC (para VFD/SERVO)
        if m.drive_type in ("VFD", "SERVO") and not ep.has_drives_emc:
            ProjectAlert.objects.create(
                project=project, level=ProjectAlert.Level.WARN,
                code="EMC_RECOMMENDED",
                message=f"Carga '{l.name}' tem {m.drive_type}. Recomenda-se marcar 'tem drives/EMC' para habilitar itens EMC.",
                context={"load_id": str(l.id)}
            )

        if m.drive_type == "DOL":
            # 1) Disjuntor do ramo (placeholder)
            BomItem.objects.create(
                bom=bom,
                category="BRANCH_BREAKER",
                description=f"Disjuntor do ramo do motor '{l.name}' (sugerido)",
                qty=1,
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={
                    "load_id": str(l.id),
                    "motor_current_a_unit": str(motor_i_unit.quantize(Decimal('0.01'))),
                    "motor_current_a_total": str(motor_i_total),
                    "suggestion": "Dimensionar In ~ 1.25×In_motor (ajustar conforme curva/aplicação)",
                },
            )

            # 2) Contator AC-3 (placeholder)
            BomItem.objects.create(
                bom=bom,
                category="CONTACTOR_AC3",
                description=f"Contator AC-3 do motor '{l.name}' (sugerido)",
                qty=1,
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={
                    "load_id": str(l.id),
                    "ac3_current_a": str(motor_i_unit.quantize(Decimal('0.01'))),
                    "coil": ep.control_voltage,
                },
            )

            # 3) Relé térmico (placeholder)
            BomItem.objects.create(
                bom=bom,
                category="OVERLOAD_RELAY",
                description=f"Relé térmico do motor '{l.name}' (sugerido)",
                qty=1,
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={
                    "load_id": str(l.id),
                    "setting_range_hint_a": str(motor_i_unit.quantize(Decimal('0.01'))),
                },
            )
        else:
            # fallback para outros tipos (mantém placeholder por enquanto)
            BomItem.objects.create(
                bom=bom,
                category="MOTOR_BRANCH",
                description=f"Ramo motor '{l.name}' ({m.drive_type}) - conjunto proteção/comando (sugerido)",
                qty=int(l.quantity),
                manufacturer="SIEMENS",
                part_number="TBD",
                meta={
                    "load_id": str(l.id),
                    "drive_type": m.drive_type,
                    "power_kw": str(m.power_kw),
                    "voltage_v": m.voltage_v,
                    "motor_current_a_unit": str(motor_i_unit.quantize(Decimal('0.01'))),
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