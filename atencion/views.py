from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg
from django.http import HttpResponse

from io import BytesIO
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet

from .models import (
    Coordinador,
    Periodo,
    Evaluacion,
    ConductaSello,
    Objetivo,
    RespuestaConducta,
    RespuestaObjetivo,
)


# -------- Helpers: detectar campo de puntaje real --------

def _score_field(model_cls, preferred=("puntaje", "cumplimiento", "score", "valor")):
    """
    Retorna el nombre del campo real para puntaje en un modelo.
    En tu caso, RespuestaConducta/RespuestaObjetivo tienen "cumplimiento" (CharField),
    así que lo usa como valor.
    """
    field_names = {f.name for f in model_cls._meta.get_fields() if hasattr(f, "name")}
    for n in preferred:
        if n in field_names:
            return n
    return None


RESP_COND_FIELD = _score_field(RespuestaConducta, preferred=("puntaje", "cumplimiento", "score", "valor"))
RESP_OBJ_FIELD  = _score_field(RespuestaObjetivo, preferred=("puntaje", "cumplimiento", "score", "valor"))


def _promedio_respuestas(qs, field_name):
    if not field_name:
        return None
    # Si es CharField (como "cumplimiento"), promediamos manualmente convirtiendo a float cuando se pueda.
    vals = []
    for r in qs:
        v = getattr(r, field_name, None)
        if v is None:
            continue
        s = str(v).strip()
        try:
            vals.append(float(s))
        except Exception:
            continue
    if not vals:
        return None
    return sum(vals) / len(vals)


def _calcular_score(evaluacion: Evaluacion):
    """
    Promedio simple: promedio conductas + promedio objetivos.
    """
    prom_c = _promedio_respuestas(
        RespuestaConducta.objects.filter(evaluacion=evaluacion),
        RESP_COND_FIELD
    )
    prom_o = _promedio_respuestas(
        RespuestaObjetivo.objects.filter(evaluacion=evaluacion),
        RESP_OBJ_FIELD
    )

    vals = [v for v in [prom_c, prom_o] if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _equivalente_0_120(score_1_5):
    """
    Convierte score 1–5 a equivalente 0–120:
    1.0 -> 24
    5.0 -> 120
    (lineal)
    """
    if score_1_5 is None:
        return None
    try:
        s = float(score_1_5)
    except Exception:
        return None
    return (s / 5.0) * 120.0


def _nivel_desempeno(equiv_0_120):
    """
    Rangos (números):
    - No logrado: 0 - 79.9999
    - Parcialmente logrado: 80 - 95.9999
    - Esperado: 96 - 109.9999
    - Destacado: 110 - 120
    """
    if equiv_0_120 is None:
        return ("Sin datos", "gris")

    e = float(equiv_0_120)

    if e < 80:
        return ("No logrado", "rojo")
    if 80 <= e < 96:
        return ("Parcialmente logrado", "amarillo")
    if 96 <= e < 110:
        return ("Esperado", "verde")
    return ("Destacado", "azul")


def _anio_desde_periodo(periodo_name: str):
    if not periodo_name:
        return timezone.now().year
    m = re.search(r"(20\d{2})", periodo_name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return timezone.now().year


def _numero_acta(evaluacion: Evaluacion):
    """
    Número de acta automático:
    ACTA-ARICA-COORD-<AÑO>-<ID 4 dígitos>
    """
    anio = _anio_desde_periodo(getattr(evaluacion.periodo, "name", ""))
    return f"ACTA-ARICA-COORD-{anio}-{evaluacion.id:04d}"


# -------- Views --------

def dashboard_gestion(request):
    periodos = Periodo.objects.all().order_by("-id")

    periodo_id = request.GET.get("periodo")
    periodo_sel = None
    if periodo_id:
        try:
            periodo_sel = Periodo.objects.get(id=int(periodo_id))
        except (ValueError, Periodo.DoesNotExist):
            periodo_sel = None

    coordinadores = Coordinador.objects.filter(is_active=True).order_by("nombre_completo")

    eval_por_coord = {}
    if periodo_sel:
        qs = Evaluacion.objects.filter(periodo=periodo_sel).select_related("coordinador", "periodo")
        for e in qs:
            eval_por_coord[e.coordinador_id] = e

    filas = []
    if periodo_sel:
        for c in coordinadores:
            e = eval_por_coord.get(c.id)
            if e:
                score = _calcular_score(e)
                equivalente = _equivalente_0_120(score)
                nivel, nivel_color = _nivel_desempeno(equivalente)
                accion = ("ver", e.id)
            else:
                score = None
                equivalente = None
                nivel, nivel_color = ("Sin evaluación", "gris")
                accion = ("crear", c.id)

            filas.append(
                {
                    "coordinador": c,
                    "evaluacion": e,
                    "score": score,
                    "equivalente": equivalente,
                    "nivel": nivel,
                    "nivel_color": nivel_color,
                    "accion": accion,
                }
            )

    ctx = {
        "periodos": periodos,
        "periodo_sel": periodo_sel,
        "filas": filas,
        "hay_periodo": bool(periodo_sel),
        "hay_coordinadores": coordinadores.exists(),
    }
    return render(request, "dashboard_list.html", ctx)


def crear_evaluacion(request, coordinador_id: int, periodo_id: int):
    coordinador = get_object_or_404(Coordinador, id=coordinador_id, is_active=True)
    periodo = get_object_or_404(Periodo, id=periodo_id)

    evaluacion, _ = Evaluacion.objects.get_or_create(
        coordinador=coordinador,
        periodo=periodo,
        defaults={
            "fecha_creacion": timezone.now(),
            "cerrada": False,
        },
    )
    return redirect("evaluacion_detalle", evaluacion_id=evaluacion.id)


def evaluacion_detalle(request, evaluacion_id: int):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
    coordinador = evaluacion.coordinador
    periodo = evaluacion.periodo

    conductas = ConductaSello.objects.all().order_by("id")

    objetivos_qs = Objetivo.objects.all().order_by("id")
    pauta = getattr(evaluacion, "pauta", None)
    if pauta is not None:
        try:
            objetivos_qs = Objetivo.objects.filter(pauta=pauta).order_by("id")
        except Exception:
            objetivos_qs = Objetivo.objects.all().order_by("id")
    objetivos = objetivos_qs

    resp_conductas_qs = RespuestaConducta.objects.filter(evaluacion=evaluacion).select_related("conducta")
    resp_objetivos_qs = RespuestaObjetivo.objects.filter(evaluacion=evaluacion).select_related("objetivo")

    resp_conductas = {r.conducta_id: r for r in resp_conductas_qs}
    resp_objetivos = {r.objetivo_id: r for r in resp_objetivos_qs}

    if request.method == "POST":
        if evaluacion.cerrada:
            messages.warning(request, "La evaluación está cerrada y no se puede modificar.")
            return redirect("evaluacion_detalle", evaluacion_id=evaluacion.id)

        # Guardar conductas
        for c in conductas:
            key_p = f"conducta_{c.id}"
            val = (request.POST.get(key_p) or "").strip()
            puntaje = val if val != "" else ""

            # Si no hay nada y no existía, omitir
            if puntaje == "" and (c.id not in resp_conductas):
                continue

            RespuestaConducta.objects.update_or_create(
                evaluacion=evaluacion,
                conducta=c,
                defaults={"cumplimiento": puntaje},
            )

        # Guardar objetivos
        for o in objetivos:
            key_p = f"objetivo_{o.id}"
            val = (request.POST.get(key_p) or "").strip()
            puntaje = val if val != "" else ""

            if puntaje == "" and (o.id not in resp_objetivos):
                continue

            RespuestaObjetivo.objects.update_or_create(
                evaluacion=evaluacion,
                objetivo=o,
                defaults={"cumplimiento": puntaje},
            )

        # Comentarios finales
        evaluacion.fortalezas = request.POST.get("fortalezas", "").strip()
        evaluacion.oportunidades_mejora = request.POST.get("oportunidades_mejora", "").strip()
        evaluacion.resumen_comentarios = request.POST.get("resumen_comentarios", "").strip()
        evaluacion.retroalimentacion = request.POST.get("retroalimentacion", "").strip()
        evaluacion.save()

        # Cerrar evaluación
        if request.POST.get("accion") == "cerrar":
            evaluacion.cerrada = True
            evaluacion.save(update_fields=["cerrada"])
            messages.success(request, "Evaluación cerrada. Ya no se puede editar.")
        else:
            messages.success(request, "Cambios guardados correctamente.")

        return redirect("evaluacion_detalle", evaluacion_id=evaluacion.id)

    score = _calcular_score(evaluacion)
    equivalente = _equivalente_0_120(score)
    nivel, nivel_color = _nivel_desempeno(equivalente)

    ctx = {
        "evaluacion": evaluacion,
        "coordinador": coordinador,
        "periodo": periodo,
        "score": score,
        "equivalente": equivalente,
        "nivel": nivel,
        "nivel_color": nivel_color,
        "conductas": conductas,
        "objetivos": objetivos,
        "resp_conductas": resp_conductas,
        "resp_objetivos": resp_objetivos,
    }
    return render(request, "evaluacion_detalle.html", ctx)


# ---------- ACTA (HTML + PDF) ----------

def acta_evaluacion(request, evaluacion_id: int):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
    coordinador = evaluacion.coordinador
    periodo = evaluacion.periodo

    conductas = ConductaSello.objects.all().order_by("id")
    objetivos = Objetivo.objects.all().order_by("id")

    resp_conductas_qs = RespuestaConducta.objects.filter(evaluacion=evaluacion).select_related("conducta")
    resp_objetivos_qs = RespuestaObjetivo.objects.filter(evaluacion=evaluacion).select_related("objetivo")

    resp_conductas = {r.conducta_id: r for r in resp_conductas_qs}
    resp_objetivos = {r.objetivo_id: r for r in resp_objetivos_qs}

    score = _calcular_score(evaluacion)
    equivalente = _equivalente_0_120(score)
    nivel, nivel_color = _nivel_desempeno(equivalente)

    numero_acta = _numero_acta(evaluacion)
    fecha_firma = timezone.localdate()  # hoy (puedes cambiar a fecha_creacion si prefieres)

    # Si piden PDF
    if request.GET.get("format") == "pdf":
        return _acta_pdf_response(
            evaluacion=evaluacion,
            coordinador=coordinador,
            periodo=periodo,
            score=score,
            equivalente=equivalente,
            nivel=nivel,
            numero_acta=numero_acta,
            fecha_firma=fecha_firma,
            conductas=conductas,
            objetivos=objetivos,
            resp_conductas=resp_conductas,
            resp_objetivos=resp_objetivos,
        )

    # HTML
    ctx = {
        "evaluacion": evaluacion,
        "coordinador": coordinador,
        "periodo": periodo,
        "score": score,
        "equivalente": equivalente,
        "nivel": nivel,
        "nivel_color": nivel_color,
        "numero_acta": numero_acta,
        "fecha_firma": fecha_firma,
        "conductas": conductas,
        "objetivos": objetivos,
        "resp_conductas": resp_conductas,
        "resp_objetivos": resp_objetivos,
    }
    return render(request, "acta_evaluacion.html", ctx)


def _acta_pdf_response(
    evaluacion,
    coordinador,
    periodo,
    score,
    equivalente,
    nivel,
    numero_acta,
    fecha_firma,
    conductas,
    objetivos,
    resp_conductas,
    resp_objetivos,
):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Acta Evaluación Coordinador",
    )

    styles = getSampleStyleSheet()
    story = []

    # Encabezado oficial
    story.append(Paragraph("<b>INSTITUTO PROFESIONAL INACAP — SEDE ARICA</b>", styles["Title"]))
    story.append(Paragraph(f"<b>Evaluación de Desempeño Coordinador 2025</b>", styles["Heading2"]))
    story.append(Paragraph(f"<b>N° Acta:</b> {numero_acta}", styles["Normal"]))
    story.append(Paragraph(f"<b>Fecha de firma:</b> {fecha_firma.strftime('%d-%m-%Y')}", styles["Normal"]))
    story.append(Spacer(1, 8))

    # Meta
    meta_data = [
        ["Coordinador evaluado:", coordinador.nombre_completo],
        ["Periodo:", periodo.name],
        ["Fecha evaluación:", evaluacion.fecha_creacion.strftime("%d-%m-%Y %H:%M")],
        ["Resultado (1–5):", f"{score:.2f}" if score is not None else "—"],
        ["Equivalente (0–120):", f"{equivalente:.1f}" if equivalente is not None else "—"],
        ["Nivel:", nivel],
    ]
    meta_table = Table(meta_data, colWidths=[55 * mm, 120 * mm])
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Conductas
    story.append(Paragraph("<b>Conductas Sello</b>", styles["Heading3"]))
    cond_rows = [["Conducta", "Ponderación", "Cumplimiento"]]
    for c in conductas:
        r = resp_conductas.get(c.id)
        cond_rows.append([c.conducta, f"{c.ponderacion}%", (r.cumplimiento if r else "—")])
    cond_table = Table(cond_rows, colWidths=[110 * mm, 30 * mm, 35 * mm])
    cond_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(cond_table)
    story.append(Spacer(1, 12))

    # Objetivos
    story.append(Paragraph("<b>Objetivos de Gestión</b>", styles["Heading3"]))
    obj_rows = [["Objetivo", "Ponderación", "Cumplimiento"]]
    for o in objetivos:
        r = resp_objetivos.get(o.id)
        obj_rows.append([o.objetivo, f"{o.ponderacion}%", (r.cumplimiento if r else "—")])
    obj_table = Table(obj_rows, colWidths=[110 * mm, 30 * mm, 35 * mm])
    obj_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(obj_table)
    story.append(Spacer(1, 12))

    # Comentarios
    story.append(Paragraph("<b>Comentarios</b>", styles["Heading3"]))
    comm_data = [
        ["Fortalezas", evaluacion.fortalezas or "—"],
        ["Oportunidades de mejora", evaluacion.oportunidades_mejora or "—"],
        ["Resumen", evaluacion.resumen_comentarios or "—"],
        ["Retroalimentación", evaluacion.retroalimentacion or "—"],
    ]
    comm_table = Table(comm_data, colWidths=[55 * mm, 120 * mm])
    comm_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(comm_table)
    story.append(Spacer(1, 22))

    # Firmas
    firmas = Table(
        [
            ["", ""],
            ["______________________________", "______________________________"],
            ["Cristian Moscoso Muñoz", coordinador.nombre_completo],
            ["Director de Carrera", "Coordinador(a) de Carrera"],
            ["INACAP Sede Arica", ""],
        ],
        colWidths=[85 * mm, 85 * mm]
    )
    firmas.setStyle(TableStyle([
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, 1), 18),
    ]))
    story.append(firmas)

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    filename = f"acta_{numero_acta}.pdf"
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp
