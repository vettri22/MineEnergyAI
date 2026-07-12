"""
reports/pdf_generator.py
---------------------------
Generates professional-looking PDF reports (daily or monthly) using
ReportLab, including a summary table, KPI highlights, and per-machine
breakdown.
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)

from config import Config

BRAND_COLOR = colors.HexColor("#0B5FFF")
DARK_COLOR = colors.HexColor("#101828")
LIGHT_GREY = colors.HexColor("#F4F6FA")


def generate_pdf_report(report_type, period_label, kpis, rows, output_dir=None):
    """
    Build a PDF report file and return its full path.

    Args:
        report_type: "Daily" or "Monthly"
        period_label: human readable period string, e.g. "12 June 2026"
        kpis: dict with keys total_energy, total_cost, total_carbon,
              avg_efficiency, machine_count, alert_count
        rows: list of dicts with per-machine data:
              {machine_code, machine_name, machine_type, energy_kwh,
               ore_processed, efficiency_score, status}
    """
    output_dir = output_dir or Config.REPORTS_FOLDER
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"MineEnergyAI_{report_type}_Report_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=DARK_COLOR, fontSize=20, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles["Normal"], textColor=colors.grey, fontSize=10
    )
    section_style = ParagraphStyle(
        "SectionStyle", parent=styles["Heading2"], textColor=BRAND_COLOR, spaceBefore=14, spaceAfter=8
    )

    elements = []
    elements.append(Paragraph("MineEnergy AI &mdash; Intelligent Energy Management", title_style))
    elements.append(Paragraph(
        f"{report_type} Energy &amp; Efficiency Report &nbsp;|&nbsp; Period: {period_label}",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", color=BRAND_COLOR, thickness=1.2))
    elements.append(Spacer(1, 14))

    # KPI summary table
    elements.append(Paragraph("Executive Summary", section_style))
    kpi_data = [
        ["Total Energy (kWh)", "Electricity Cost (INR)", "Carbon Emission (kg)"],
        [f"{kpis['total_energy']:,.1f}", f"{kpis['total_cost']:,.2f}", f"{kpis['total_carbon']:,.1f}"],
        ["Avg. Efficiency Score", "Machines Monitored", "Open Alerts"],
        [f"{kpis['avg_efficiency']:.1f} / 100", f"{kpis['machine_count']}", f"{kpis['alert_count']}"],
    ]
    kpi_table = Table(kpi_data, colWidths=[5.5 * cm] * 3)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("BACKGROUND", (0, 2), (-1, 2), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GREY),
        ("BACKGROUND", (0, 3), (-1, 3), LIGHT_GREY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 18))

    # Per-machine breakdown table
    elements.append(Paragraph("Machine-wise Energy Breakdown", section_style))
    table_header = ["Code", "Machine", "Type", "Energy (kWh)", "Ore (T)", "Efficiency", "Status"]
    table_data = [table_header]
    for r in rows:
        table_data.append([
            r["machine_code"], r["machine_name"], r["machine_type"],
            f"{r['energy_kwh']:,.1f}", f"{r['ore_processed']:,.1f}",
            f"{r['efficiency_score']:.1f}", r["status"],
        ])

    machine_table = Table(table_data, colWidths=[2.0 * cm, 3.6 * cm, 3.0 * cm, 2.6 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E0E4EA")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    machine_table.setStyle(TableStyle(style_cmds))
    elements.append(machine_table)

    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#E0E4EA"), thickness=0.8))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Generated by MineEnergy AI on {datetime.now().strftime('%d %b %Y, %H:%M')}. "
        "This report is system-generated and intended for internal operational use.",
        footer_style
    ))

    doc.build(elements)
    return filepath
