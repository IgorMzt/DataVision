from __future__ import annotations

from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def export_csv(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    buf.write(df.to_csv(index=False).encode("utf-8-sig"))
    buf.seek(0)
    return buf


def export_excel(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados processados")
        ws = writer.book["Dados processados"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for column in ws.columns:
            letter = column[0].column_letter
            width = min(max((len(str(cell.value or "")) for cell in column), default=10) + 2, 40)
            ws.column_dimensions[letter].width = width
    buf.seek(0)
    return buf


def export_chart_png(chart: dict) -> BytesIO:
    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    labels, values = chart.get("labels", []), chart.get("values", [])
    if chart.get("type") == "line":
        ax.plot(labels, values, marker="o")
    elif chart.get("type") == "doughnut":
        ax.pie(values, labels=labels, autopct="%1.1f%%", wedgeprops={"width": .42})
    else:
        ax.bar([str(x) for x in labels], values)
        ax.tick_params(axis="x", rotation=35)
    ax.set_title(chart.get("title", "DataVision"))
    if chart.get("type") != "doughnut":
        ax.grid(axis="y", alpha=.18)
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def export_pdf(project, run, analytics: dict, anomalies: dict) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("DVTitle", parent=styles["Title"], fontSize=22, leading=27, spaceAfter=8)
    small = ParagraphStyle("DVSmall", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#52657a"))
    story = [Paragraph("DataVision - Relatorio Executivo", title), Paragraph(f"Projeto: {project.name} | Segmento: {analytics.get('segment_label')} | Execucao #{run.id}", small), Spacer(1, 8)]
    story.append(Paragraph("Indicadores", styles["Heading2"]))
    kpi_data = [["Indicador", "Valor", "Contexto"]] + [[str(k.get("label","")), str(k.get("value","")), str(k.get("hint",""))] for k in analytics.get("kpis", [])]
    table = Table(kpi_data, colWidths=[50*mm, 48*mm, 65*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#10253d")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.HexColor("#ccd5df")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)]))
    story += [table, Spacer(1, 12), Paragraph("Insights", styles["Heading2"])]
    for item in analytics.get("insights", []):
        story.append(Paragraph(f"<b>{item.get('title','')}</b> - {item.get('text','')}", styles["BodyText"]))
        story.append(Spacer(1, 5))
    story += [Spacer(1, 8), Paragraph("Anomalias", styles["Heading2"]), Paragraph(anomalies.get("disclaimer") or "Sem componentes suficientes para analise.", small)]
    summary = anomalies.get("summary") or {}
    if anomalies.get("available"):
        story.append(Paragraph(f"Alto: {summary.get('high',0)} | Moderado: {summary.get('moderate',0)} | Maior score: {summary.get('max_score',0)}", styles["BodyText"]))
    story += [Spacer(1, 12), Paragraph("Nota metodologica", styles["Heading2"]), Paragraph("Os insights e scores desta versao sao calculados por regras e estatistica. Anomaly Score mede desvio do padrao observado e nao representa probabilidade de fraude.", styles["BodyText"])]
    doc.build(story)
    buf.seek(0)
    return buf
