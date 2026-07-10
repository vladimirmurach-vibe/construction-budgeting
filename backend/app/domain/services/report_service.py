"""ReportService — Excel (openpyxl) + PDF (ReportLab или fallback), ASM-004."""
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.services.aggregation_service import AggregationService
from app.infrastructure.db.models import FinancialResult, Report, ReportFormat, ReportType


def _write_simple_pdf(file_path: str, title: str, headers: list[str], rows: list[list]):
    """Минимальный PDF без внешних зависимостей (fallback при отсутствии ReportLab)."""
    safe_title = "Financial Report"
    objects = []
    y = 750
    objects.append(f"BT /F1 14 Tf 50 {y} Td ({safe_title}) Tj ET")
    y -= 30
    header_line = " | ".join(headers)
    objects.append(f"BT /F1 10 Tf 50 {y} Td ({header_line}) Tj ET")
    y -= 14
    for row in rows:
        line = " | ".join(str(c) for c in row)[:100]
        objects.append(f"BT /F1 10 Tf 50 {y} Td ({line}) Tj ET")
        y -= 14
        if y < 50:
            break

    stream = "\n".join(objects)
    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length {len(stream)}>>stream
{stream}
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000400 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
500
%%EOF"""
    with open(file_path, "wb") as f:
        f.write(pdf.encode("latin-1", errors="replace"))


class ReportService:
    def __init__(self):
        self.aggregation = AggregationService()
        Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        db: Session,
        scenario_id: UUID,
        report_type: ReportType,
        report_format: ReportFormat,
        construction_object_id: UUID | None = None,
    ) -> Report:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ext = "xlsx" if report_format == ReportFormat.excel else "pdf"
        filename = f"report_{scenario_id}_{report_type.value}_{timestamp}.{ext}"
        file_path = os.path.join(settings.reports_dir, filename)

        if report_format == ReportFormat.excel:
            self._generate_excel(db, scenario_id, report_type, file_path, construction_object_id)
        else:
            self._generate_pdf(db, scenario_id, report_type, file_path, construction_object_id)

        report = Report(
            scenario_id=scenario_id,
            format=report_format,
            type=report_type,
            file_path=file_path,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def _get_data(self, db, scenario_id, report_type, construction_object_id):
        if report_type == ReportType.consolidated:
            return self.aggregation.get_consolidated(db, scenario_id)
        query = db.query(FinancialResult).filter(
            FinancialResult.scenario_id == scenario_id,
            FinancialResult.is_consolidated == False,  # noqa: E712
        )
        if construction_object_id:
            query = query.filter(FinancialResult.construction_object_id == construction_object_id)
        rows = query.order_by(FinancialResult.period).all()
        return [
            {
                "period": r.period,
                "revenue": float(r.revenue),
                "costs": float(r.costs),
                "profit": float(r.profit),
            }
            for r in rows
        ]

    def _generate_excel(self, db, scenario_id, report_type, file_path, construction_object_id):
        data = self._get_data(db, scenario_id, report_type, construction_object_id)
        wb = Workbook()
        ws = wb.active
        ws.title = "Финансовый результат"
        ws.append(["Период", "Выручка", "Затраты", "Прибыль"])
        for row in data:
            ws.append([row["period"], row["revenue"], row["costs"], row["profit"]])
        wb.save(file_path)

    def _generate_pdf(self, db, scenario_id, report_type, file_path, construction_object_id):
        data = self._get_data(db, scenario_id, report_type, construction_object_id)
        headers = ["Период", "Выручка", "Затраты", "Прибыль"]
        rows = [
            [r["period"], f"{r['revenue']:,.2f}", f"{r['costs']:,.2f}", f"{r['profit']:,.2f}"]
            for r in data
        ]
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = [
                Paragraph("Отчёт: консолидированный финансовый результат", styles["Title"]),
                Spacer(1, 12),
            ]
            table_data = [headers] + rows
            table = Table(table_data)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(table)
            doc.build(elements)
        except ImportError:
            _write_simple_pdf(file_path, "Консолидированный финансовый результат", headers, rows)
