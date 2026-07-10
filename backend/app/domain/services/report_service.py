from pathlib import Path

from openpyxl import Workbook


class ReportService:
    def generate_excel(self, file_path: Path, scenario, results) -> Path:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Financial Results"
        sheet.append(["Scenario", scenario.name])
        sheet.append([])
        sheet.append(["Period", "Object ID", "Revenue", "Costs", "Profit", "Consolidated"])
        for result in results:
            sheet.append(
                [
                    result.period,
                    result.construction_object_id,
                    result.revenue,
                    result.costs,
                    result.profit,
                    result.is_consolidated,
                ]
            )
        workbook.save(file_path)
        return file_path

    def generate_pdf(self, file_path: Path, scenario, results) -> Path:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            pdf = canvas.Canvas(str(file_path), pagesize=A4)
            _, height = A4
            y = height - 40
            pdf.drawString(40, y, f"Scenario: {scenario.name}")
            y -= 30
            for result in results[:40]:
                pdf.drawString(
                    40,
                    y,
                    f"{result.period} revenue={result.revenue:.2f} costs={result.costs:.2f} profit={result.profit:.2f}",
                )
                y -= 16
                if y < 40:
                    pdf.showPage()
                    y = height - 40
            pdf.save()
        except Exception:
            file_path.write_text(
                f"PDF report fallback\nScenario: {scenario.name}\nRows: {len(results)}\n",
                encoding="utf-8",
            )
        return file_path
