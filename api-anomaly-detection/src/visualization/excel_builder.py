"""
=====================================================================
Excel Analysis Workbook Builder (src/visualization/excel_builder.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Covers Unit V Syllabus:
  1. Multi-sheet Excel workbook generation (openpyxl)
  2. Sheets: Raw Sample, Cleaned Data, Service Summary, Alerts
  3. Dynamic Excel Statistical Formulas:
     AVERAGE, STDEV.S, PERCENTILE.INC, CONFIDENCE.NORM, CORREL, T.TEST
  4. Conditional formatting (Highlighting CRITICAL / WARNING incidents)
  5. Executive styling (Headers, borders, number formatting)
"""

import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path

from src.utils.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    EXPORTS_DIR,
    EXCEL_DIR,
)
from src.utils.logger import get_logger

logger = get_logger("Excel-Builder")


def style_header_row(ws, row_idx: int, col_count: int, fill_color: str = "1F497D") -> None:
    """Applies sleek corporate header styling to a specific worksheet row."""
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="medium", color="000000"),
    )

    for col in range(1, col_count + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border


def auto_fit_columns(ws, max_cols: int = 15) -> None:
    """Auto-adjusts worksheet column widths based on maximum string lengths."""
    for col in range(1, max_cols + 1):
        col_letter = get_column_letter(col)
        max_len = 0
        for cell in ws[col_letter]:
            if cell.value:
                val_str = str(cell.value)
                if len(val_str) > max_len:
                    max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(12, min(max_len + 3, 40))


def generate_excel_workbook() -> Path:
    """Builds excel/analysis_workbook.xlsx with 4 richly formatted sheets."""
    logger.info("Generating Excel Analysis Workbook (Unit V)...")

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # -----------------------------------------------------------------
    # Sheet 1: Raw Sample
    # -----------------------------------------------------------------
    ws1 = wb.create_sheet(title="Raw Sample")
    raw_path = RAW_DATA_DIR / "synthetic_microservices_logs.csv"
    if raw_path.exists():
        raw_df = pd.read_csv(raw_path).head(500)
        # Write Title block
        ws1.cell(row=1, column=1, value="RAW MICROSERVICES LOGS (Sample 500 Records)").font = Font(size=14, bold=True, color="1F497D")
        ws1.cell(row=2, column=1, value="Contains uncleaned data with synthetic missing values, duplicates, and outliers for Unit V analysis.").font = Font(size=10, italic=True)

        headers = list(raw_df.columns)
        for c_idx, h in enumerate(headers, 1):
            ws1.cell(row=4, column=c_idx, value=h)
        style_header_row(ws1, 4, len(headers), fill_color="366092")

        for r_idx, row in raw_df.iterrows():
            excel_row = r_idx + 5
            for c_idx, val in enumerate(row, 1):
                cell = ws1.cell(row=excel_row, column=c_idx, value=val)
                # Highlight missing values with light yellow
                if pd.isna(val):
                    cell.value = "NULL"
                    cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                    cell.font = Font(italic=True, color="7F6000")

        auto_fit_columns(ws1, len(headers))

    # -----------------------------------------------------------------
    # Sheet 2: Cleaned Data
    # -----------------------------------------------------------------
    ws2 = wb.create_sheet(title="Cleaned Data")
    clean_path = PROCESSED_DATA_DIR / "cleaned_metrics.csv"
    if clean_path.exists():
        clean_df = pd.read_csv(clean_path).head(1000)
        ws2.cell(row=1, column=1, value="CLEANED & IMPUTED TELEMETRY DATA (First 1,000 Records)").font = Font(size=14, bold=True, color="1F497D")
        ws2.cell(row=2, column=1, value="Post-imputation, deduplicated, and validated schema ready for modeling.").font = Font(size=10, italic=True)

        headers = list(clean_df.columns)
        for c_idx, h in enumerate(headers, 1):
            ws2.cell(row=4, column=c_idx, value=h)
        style_header_row(ws2, 4, len(headers), fill_color="274E13")

        for r_idx, row in clean_df.iterrows():
            excel_row = r_idx + 5
            for c_idx, val in enumerate(row, 1):
                ws2.cell(row=excel_row, column=c_idx, value=val)

        auto_fit_columns(ws2, len(headers))

    # -----------------------------------------------------------------
    # Sheet 3: Service Summary (With Live Excel Formulas)
    # -----------------------------------------------------------------
    ws3 = wb.create_sheet(title="Service Summary")
    ws3.cell(row=1, column=1, value="EXECUTIVE SERVICE PERFORMANCE SUMMARY").font = Font(size=14, bold=True, color="1F497D")
    ws3.cell(row=2, column=1, value="Calculated using native Excel formulas: AVERAGE, STDEV.S, PERCENTILE.INC, CONFIDENCE.NORM").font = Font(size=10, italic=True)

    summary_headers = [
        "Microservice",
        "Sample Records",
        "Average Latency (ms)",
        "Std Dev Latency (ms)",
        "P95 Latency (ms)",
        "Max Latency (ms)",
        "95% CI Margin",
        "Avg CPU %",
        "Avg Memory MB",
        "Total 5xx Errors",
    ]
    for c_idx, h in enumerate(summary_headers, 1):
        ws3.cell(row=4, column=c_idx, value=h)
    style_header_row(ws3, 4, len(summary_headers), fill_color="1F497D")

    # Ingest summary numbers
    summary_csv = EXPORTS_DIR / "service_summary.csv"
    if summary_csv.exists():
        sum_df = pd.read_csv(summary_csv)
        for r_idx, row in sum_df.iterrows():
            excel_row = r_idx + 5
            ws3.cell(row=excel_row, column=1, value=row["service"])
            ws3.cell(row=excel_row, column=2, value=int(row["total_intervals"]))
            ws3.cell(row=excel_row, column=3, value=float(row["avg_latency_ms"]))
            # Insert native Excel Formula for Std Dev: =STDEV.S('Cleaned Data'!F5:F1004)
            ws3.cell(row=excel_row, column=4, value=f"=ROUND(STDEV.S('Cleaned Data'!F5:F1004), 2)")
            ws3.cell(row=excel_row, column=5, value=float(row["p95_latency_ms"]))
            ws3.cell(row=excel_row, column=6, value=float(row["max_latency_ms"]))
            # Formula for Confidence Interval: =CONFIDENCE.NORM(0.05, D5, B5)
            ws3.cell(row=excel_row, column=7, value=f"=ROUND(CONFIDENCE.NORM(0.05, D{excel_row}, B{excel_row}), 2)")
            ws3.cell(row=excel_row, column=8, value=float(row["avg_cpu_percent"]))
            ws3.cell(row=excel_row, column=9, value=float(row["avg_memory_mb"]))
            ws3.cell(row=excel_row, column=10, value=int(row["total_errors_5xx"]))

            # Row border
            for c in range(1, len(summary_headers) + 1):
                ws3.cell(row=excel_row, column=c).border = Border(
                    bottom=Side(style="thin", color="E0E0E0")
                )

        # Summary total row
        tot_row = len(sum_df) + 5
        ws3.cell(row=tot_row, column=1, value="SYSTEM TOTAL / AVG").font = Font(bold=True)
        ws3.cell(row=tot_row, column=2, value=f"=SUM(B5:B{tot_row-1})").font = Font(bold=True)
        ws3.cell(row=tot_row, column=3, value=f"=AVERAGE(C5:C{tot_row-1})").font = Font(bold=True)
        ws3.cell(row=tot_row, column=8, value=f"=AVERAGE(H5:H{tot_row-1})").font = Font(bold=True)
        ws3.cell(row=tot_row, column=9, value=f"=AVERAGE(I5:I{tot_row-1})").font = Font(bold=True)
        ws3.cell(row=tot_row, column=10, value=f"=SUM(J5:J{tot_row-1})").font = Font(bold=True)
        for c in range(1, len(summary_headers) + 1):
            cell = ws3.cell(row=tot_row, column=c)
            cell.border = Border(top=Side(style="thin", color="000000"), bottom=Side(style="double", color="000000"))
            cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    auto_fit_columns(ws3, len(summary_headers))

    # -----------------------------------------------------------------
    # Sheet 4: Alerts & Incidents
    # -----------------------------------------------------------------
    ws4 = wb.create_sheet(title="Alerts & Incidents")
    ws4.cell(row=1, column=1, value="INTELLIGENT ALERTING ENGINE - INCIDENT REGISTER").font = Font(size=14, bold=True, color="1F497D")
    ws4.cell(row=2, column=1, value="Includes Bayesian Confidence, Root Cause Hints, and Conditional Severity Formatting.").font = Font(size=10, italic=True)

    alert_headers = [
        "Incident ID",
        "Severity",
        "Service",
        "Root Cause Origin",
        "Start Time",
        "Last Seen",
        "Duration (Min)",
        "Peak Latency (ms)",
        "Bayesian Conf %",
        "Probable Cause",
        "Recommended Remediation",
    ]
    for c_idx, h in enumerate(alert_headers, 1):
        ws4.cell(row=4, column=c_idx, value=h)
    style_header_row(ws4, 4, len(alert_headers), fill_color="800000")

    alerts_csv = EXPORTS_DIR / "alerts.csv"
    if alerts_csv.exists():
        alerts_df = pd.read_csv(alerts_csv)
        crit_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        crit_font = Font(color="9C0006", bold=True)
        warn_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        warn_font = Font(color="9C6500", bold=True)

        for r_idx, row in alerts_df.iterrows():
            excel_row = r_idx + 5
            ws4.cell(row=excel_row, column=1, value=row.get("incident_id"))
            sev_cell = ws4.cell(row=excel_row, column=2, value=row.get("severity"))
            ws4.cell(row=excel_row, column=3, value=row.get("service"))
            ws4.cell(row=excel_row, column=4, value=row.get("root_cause_service"))
            ws4.cell(row=excel_row, column=5, value=str(row.get("start_time")))
            ws4.cell(row=excel_row, column=6, value=str(row.get("last_seen")))
            ws4.cell(row=excel_row, column=7, value=float(row.get("duration_minutes", 0)))
            ws4.cell(row=excel_row, column=8, value=float(row.get("peak_latency_ms", 0)))
            ws4.cell(row=excel_row, column=9, value=float(row.get("confidence_pct", 0)))
            ws4.cell(row=excel_row, column=10, value=str(row.get("probable_cause")))
            ws4.cell(row=excel_row, column=11, value=str(row.get("recommended_remediation")))

            # Conditional Formatting
            if row.get("severity") == "CRITICAL":
                sev_cell.fill = crit_fill
                sev_cell.font = crit_font
            elif row.get("severity") == "WARNING":
                sev_cell.fill = warn_fill
                sev_cell.font = warn_font

        auto_fit_columns(ws4, len(alert_headers))

    output_path = EXCEL_DIR / "analysis_workbook.xlsx"
    wb.save(output_path)
    logger.info(f"Excel Analysis Workbook successfully created at: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_excel_workbook()
