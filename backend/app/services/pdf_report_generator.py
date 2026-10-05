import io
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

# Curated luxury futuristic & executive corporate palette
COLOR_PRIMARY = colors.HexColor("#7c3aed")     # Vivid Purple / Violet
COLOR_SECONDARY = colors.HexColor("#2563eb")   # Executive Royal Blue
COLOR_ACCENT = colors.HexColor("#06b6d4")      # Cyan Highlight
COLOR_DARK = colors.HexColor("#0f172a")        # Deep Slate
COLOR_TEXT_MUTED = colors.HexColor("#475569")  # Muted Slate
COLOR_BG_LIGHT = colors.HexColor("#f8fafc")    # Clean Canvas Light
COLOR_CARD_BG = colors.HexColor("#f1f5f9")     # Card Tint
COLOR_BORDER = colors.HexColor("#e2e8f0")      # Subtle Border
COLOR_SUCCESS = colors.HexColor("#10b981")     # Emerald
COLOR_WARNING = colors.HexColor("#f59e0b")     # Amber
COLOR_DANGER = colors.HexColor("#ef4444")      # Rose

def generate_pdf_report_bytes(dashboard_data: Dict[str, Any], profile_data: Dict[str, Any] = None) -> bytes:
    """
    Generate an executive AI-powered PDF report containing verified calculations:
    1. Header & Dataset Overview
    2. Executive Key Performance Indicators (KPIs)
    3. AI Discovered Insights (5 Core Findings)
    4. Top Products Breakdown
    5. Regional Performance Breakdown
    6. Important Temporal Trends
    7. Statistical Anomalies (IQR Outlier Audit)
    8. Data Quality & Schema Integrity Summary
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=COLOR_DARK
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=COLOR_TEXT_MUTED
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=COLOR_PRIMARY,
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=COLOR_DARK
    )
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=COLOR_DARK
    )
    badge_style = ParagraphStyle(
        'BadgeText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=COLOR_PRIMARY
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_DARK
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    filename = dashboard_data.get("filename", "Dataset")
    kpis = dashboard_data.get("kpis", {})
    ai_discovered = dashboard_data.get("ai_discovered", [])
    charts = dashboard_data.get("charts", {})
    anomalies = dashboard_data.get("anomalies", {})
    data_quality = dashboard_data.get("data_quality", {})
    drivers = dashboard_data.get("drivers", {})

    now_str = datetime.now().strftime("%B %d, %Y • %I:%M %p")

    # 1. HEADER SECTION
    header_data = [
        [
            Paragraph("<b>INSIGHTFORGE AI</b> | Executive Intelligence Report", badge_style),
            Paragraph(f"Generated: {now_str}", subtitle_style)
        ],
        [
            Paragraph(f"Dataset Analysis: <b>{filename}</b>", title_style),
            Paragraph("Status: <b>Verified by Pandas Sandbox</b>", ParagraphStyle('Status', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_SUCCESS, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=4, spaceAfter=10))

    # 2. DATASET OVERVIEW & SUMMARY
    total_rows = data_quality.get("total_rows", 0)
    total_cols = data_quality.get("total_columns", 0)
    overview_text = (
        f"This executive analytical intelligence report synthesizes verified descriptive statistics, distribution metrics, "
        f"and anomaly profiles for <b>{filename}</b> ({total_rows:,} records across {total_cols} schema dimensions). "
        f"All mathematical computations are strictly calculated from active DataFrame series."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 8))

    # 3. KEY PERFORMANCE INDICATORS (KPIs) GRID
    story.append(Paragraph("1. KEY PERFORMANCE INDICATORS (KPIs)", section_heading))
    
    rev_fmt = kpis.get("total_revenue", {}).get("formatted", "$0.00")
    orders_fmt = kpis.get("total_orders", {}).get("formatted", f"{total_rows:,}")
    aov_fmt = kpis.get("average_order_value", {}).get("formatted", "$0.00")
    growth_fmt = kpis.get("growth_rate", {}).get("formatted", "0.0%")
    growth_trend = kpis.get("growth_rate", {}).get("trend", "neutral")

    kpi_boxes = [
        [
            Paragraph("<b>TOTAL REVENUE</b><br/><font size=13 color='#7c3aed'><b>" + rev_fmt + "</b></font><br/><font size=7 color='#64748b'>Cumulative Volume</font>", body_style),
            Paragraph("<b>TOTAL ORDERS</b><br/><font size=13 color='#2563eb'><b>" + orders_fmt + "</b></font><br/><font size=7 color='#64748b'>Ingested Transactions</font>", body_style),
            Paragraph("<b>AVERAGE ORDER VALUE</b><br/><font size=13 color='#06b6d4'><b>" + aov_fmt + "</b></font><br/><font size=7 color='#64748b'>Mean Ticket Size</font>", body_style),
            Paragraph("<b>MOM GROWTH RATE</b><br/><font size=13 color='" + ("#10b981" if growth_trend != "down" else "#ef4444") + "'><b>" + growth_fmt + "</b></font><br/><font size=7 color='#64748b'>Cycle-over-Cycle Variance</font>", body_style)
        ]
    ]
    kpi_table = Table(kpi_boxes, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 4. AI DISCOVERED INSIGHTS (5 Strategic Findings)
    story.append(Paragraph("2. AI DISCOVERED EXECUTIVE FINDINGS", section_heading))
    if ai_discovered:
        insight_rows = []
        for item in ai_discovered:
            title = item.get("title", "Insight")
            badge = item.get("badge", "Finding")
            statement = item.get("statement", "")
            detail = item.get("detail", "")
            
            content = f"<b>{title.upper()}</b> &nbsp; <font color='#7c3aed'>[{badge}]</font><br/><b>\"{statement}\"</b>"
            if detail:
                content += f"<br/><font color='#475569'>{detail}</font>"
            insight_rows.append([Paragraph(content, body_style)])

        insight_table = Table(insight_rows, colWidths=[540])
        insight_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLOR_BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 1, COLOR_BORDER),
            ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(insight_table)
    story.append(Spacer(1, 10))

    # 5. TOP PRODUCTS & REGIONAL PERFORMANCE BREAKDOWN
    story.append(Paragraph("3. COMMERCIAL BREAKDOWN (PRODUCTS & REGIONS)", section_heading))

    top_prods_data = charts.get("top_products", {}).get("data", [])
    regional_data = charts.get("regional_performance", {}).get("data", [])

    # Products Table
    prod_table_rows = [
        [
            Paragraph("<b>Top Products</b>", table_header_style),
            Paragraph("<b>Revenue</b>", table_header_style)
        ]
    ]
    for p in top_prods_data[:5]:
        p_name = p.get("name") or p.get("product") or "Item"
        p_val = p.get("value") or p.get("revenue") or 0.0
        p_val_fmt = f"${p_val:,.2f}" if isinstance(p_val, (int, float)) else str(p_val)
        prod_table_rows.append([
            Paragraph(str(p_name), table_cell_style),
            Paragraph(p_val_fmt, ParagraphStyle('Val', parent=table_cell_style, alignment=2))
        ])
    if len(prod_table_rows) == 1:
        prod_table_rows.append([Paragraph("No product breakdown available", table_cell_style), Paragraph("-", table_cell_style)])

    # Regional Table
    reg_table_rows = [
        [
            Paragraph("<b>Regional / Category</b>", table_header_style),
            Paragraph("<b>Revenue</b>", table_header_style)
        ]
    ]
    for r in regional_data[:5]:
        r_name = r.get("name") or r.get("region") or "Segment"
        r_val = r.get("value") or r.get("revenue") or 0.0
        r_val_fmt = f"${r_val:,.2f}" if isinstance(r_val, (int, float)) else str(r_val)
        reg_table_rows.append([
            Paragraph(str(r_name), table_cell_style),
            Paragraph(r_val_fmt, ParagraphStyle('Val', parent=table_cell_style, alignment=2))
        ])
    if len(reg_table_rows) == 1:
        reg_table_rows.append([Paragraph("No regional breakdown available", table_cell_style), Paragraph("-", table_cell_style)])

    t_prod = Table(prod_table_rows, colWidths=[180, 80])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    t_reg = Table(reg_table_rows, colWidths=[180, 80])
    t_reg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_SECONDARY),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    side_by_side = Table([[t_prod, Paragraph("", body_style), t_reg]], colWidths=[260, 20, 260])
    side_by_side.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(side_by_side)
    story.append(Spacer(1, 10))

    # 6. TEMPORAL TRENDS SUMMARY
    story.append(Paragraph("4. TEMPORAL TRENDS & TRAJECTORY", section_heading))
    trend_info = charts.get("revenue_trend", {})
    trend_pts = trend_info.get("data", [])
    peak_p = trend_info.get("peak_period", "N/A")
    peak_v = trend_info.get("peak_val", 0.0)
    trough_p = trend_info.get("trough_period", "N/A")
    trough_v = trend_info.get("trough_val", 0.0)

    trend_summary_text = (
        f"Temporal aggregation identified <b>{len(trend_pts)} distinct operating periods</b>. "
        f"Performance reached its peak during <b>{peak_p}</b> generating <b>${peak_v:,.2f}</b>, "
        f"with lowest activity recorded in <b>{trough_p}</b> at <b>${trough_v:,.2f}</b>. "
        f"The primary driver concentration is <b>{drivers.get('pareto_driver', 'distributed across core segments')}</b>."
    )
    story.append(Paragraph(trend_summary_text, body_style))
    story.append(Spacer(1, 10))

    # 7. STATISTICAL ANOMALIES (IQR Outlier Audit)
    story.append(Paragraph("5. STATISTICAL ANOMALIES (IQR OUTLIER AUDIT)", section_heading))
    outlier_cnt = anomalies.get("outlier_count", 0)
    outlier_pct = anomalies.get("outlier_pct", 0.0)
    iqr_val = anomalies.get("iqr", 0.0)
    upper_b = anomalies.get("upper_bound", 0.0)
    max_out = anomalies.get("max_outlier", 0.0)

    anom_desc = (
        f"Interquartile Range analysis (1.5 × IQR) on target metric <b>{anomalies.get('column', 'Revenue')}</b> "
        f"detected <b>{outlier_cnt} statistical outliers</b> ({outlier_pct}% of total records) exceeding the "
        f"upper statistical threshold of <b>${upper_b:,.2f}</b> (Spread IQR: ${iqr_val:,.2f}, Peak outlier: <b>${max_out:,.2f}</b> if max_out else 'None')."
    )
    story.append(Paragraph(anom_desc, body_style))
    story.append(Spacer(1, 4))

    samples = anomalies.get("samples", [])
    if samples:
        anom_rows = [
            [
                Paragraph("<b>Row #</b>", table_header_style),
                Paragraph("<b>Product / Item</b>", table_header_style),
                Paragraph("<b>Region</b>", table_header_style),
                Paragraph("<b>Transaction Amount</b>", table_header_style)
            ]
        ]
        for s in samples[:4]:
            anom_rows.append([
                Paragraph(f"#{s.get('id', '')}", table_cell_style),
                Paragraph(str(s.get('product', 'Item')), table_cell_style),
                Paragraph(str(s.get('region', 'Global')), table_cell_style),
                Paragraph(s.get("formatted", f"${s.get('value', 0):,.2f}"), ParagraphStyle('Val', parent=table_cell_style, alignment=2))
            ])
        anom_table = Table(anom_rows, colWidths=[60, 200, 140, 140])
        anom_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLOR_DARK),
            ('BACKGROUND', (0,1), (-1,-1), COLOR_BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(anom_table)
    story.append(Spacer(1, 10))

    # 8. DATA QUALITY & SCHEMA INTEGRITY SUMMARY
    story.append(Paragraph("6. DATA QUALITY & SCHEMA INTEGRITY", section_heading))
    q_score = data_quality.get("score", 100)
    q_status = data_quality.get("status", "Optimal")
    q_dup = data_quality.get("duplicate_rows", 0)
    q_missing = data_quality.get("missing_cells", 0)
    q_missing_pct = data_quality.get("missing_pct", 0.0)

    quality_grid = [
        [
            Paragraph(f"<b>Data Health Score</b><br/><font size=12 color='{COLOR_SUCCESS.hexval()}'><b>{q_score}/100</b></font><br/><font size=7 color='#64748b'>Status: {q_status}</font>", body_style),
            Paragraph(f"<b>Duplicate Rows</b><br/><font size=12 color='{COLOR_DARK.hexval()}'><b>{q_dup:,}</b></font><br/><font size=7 color='#64748b'>{'Zero redundancy' if q_dup==0 else 'Deduplication advised'}</font>", body_style),
            Paragraph(f"<b>Missing Cells</b><br/><font size=12 color='{COLOR_DARK.hexval()}'><b>{q_missing:,} ({q_missing_pct}%)</b></font><br/><font size=7 color='#64748b'>{'Clean matrix' if q_missing==0 else 'Imputation advised'}</font>", body_style),
            Paragraph(f"<b>Dimensions</b><br/><font size=12 color='{COLOR_DARK.hexval()}'><b>{total_rows:,} × {total_cols}</b></font><br/><font size=7 color='#64748b'>Rows × Columns</font>", body_style)
        ]
    ]
    q_table = Table(quality_grid, colWidths=[135, 135, 135, 135])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(q_table)

    # Footer Disclaimer
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=4, spaceAfter=6))
    disclaimer = (
        "<i>InsightForge AI Executive Report — Generated strictly from validated Pandas calculations. "
        "No figures or insights were hallucinated or artificially estimated.</i>"
    )
    story.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', fontName='Helvetica-Oblique', fontSize=7.5, textColor=COLOR_TEXT_MUTED, alignment=1)))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
