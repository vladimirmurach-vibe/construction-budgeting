"""csv-data-source connector — импорт CSV/Excel и загрузка факта."""
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.domain.services.consensus_service import ConsensusService
from app.infrastructure.db.models import CashFlowLine, CashFlowSource, FactLoadLog


REQUIRED_COLUMNS = {
    "construction_object_code",
    "form_code",
    "line_item",
    "period",
    "base_amount",
}


class CsvDataSource:
    def read_file(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        return pd.read_csv(path)

    def validate(self, df: pd.DataFrame) -> dict:
        columns = set(df.columns.str.lower())
        missing = REQUIRED_COLUMNS - columns
        errors = []
        if missing:
            errors.append(f"Missing columns: {', '.join(sorted(missing))}")
        if "period" in columns:
            invalid = df[~df["period"].astype(str).str.match(r"^\d{4}-(0[1-9]|1[0-2])$")]
            if len(invalid) > 0:
                errors.append(f"Invalid period format in {len(invalid)} rows")
        return {"valid": len(errors) == 0, "errors": errors, "row_count": len(df)}

    def import_to_scenario(
        self,
        db: Session,
        scenario_id: UUID,
        file_path: str,
        object_code_map: dict[str, UUID],
    ) -> dict:
        df = self.read_file(file_path)
        df.columns = df.columns.str.lower()
        validation = self.validate(df)
        if not validation["valid"]:
            return {"imported": 0, "errors": validation["errors"]}

        consensus = ConsensusService()
        imported = 0
        discrepancies = []

        for _, row in df.iterrows():
            obj_code = str(row["construction_object_code"])
            if obj_code not in object_code_map:
                discrepancies.append(f"Unknown object code: {obj_code}")
                continue

            adj = row.get("adjustment", 0) or 0
            base = row["base_amount"]
            line = CashFlowLine(
                scenario_id=scenario_id,
                construction_object_id=object_code_map[obj_code],
                form_code=str(row["form_code"]),
                line_item=str(row["line_item"]),
                period=str(row["period"]),
                base_amount=float(base),
                adjustment=float(adj),
                consensus_amount=float(consensus.calculate_for_record(base, adj)),
                source=CashFlowSource.import_,
            )
            db.add(line)
            imported += 1

        db.commit()
        return {"imported": imported, "discrepancies": discrepancies}

    def load_fact_data(
        self,
        db: Session,
        file_path: str,
        object_code_map: dict[str, UUID],
    ) -> FactLoadLog:
        log = FactLoadLog(status="started", records_loaded=0)
        db.add(log)
        db.flush()

        try:
            if not os.path.exists(file_path):
                log.status = "error"
                log.message = f"File not found: {file_path}"
                db.commit()
                return log

            df = self.read_file(file_path)
            df.columns = df.columns.str.lower()
            count = 0

            for _, row in df.iterrows():
                obj_code = str(row.get("construction_object_code", ""))
                if obj_code not in object_code_map:
                    continue
                actual = row.get("actual_amount")
                if actual is None:
                    continue

                lines = db.query(CashFlowLine).filter(
                    CashFlowLine.construction_object_id == object_code_map[obj_code],
                    CashFlowLine.form_code == str(row.get("form_code", "")),
                    CashFlowLine.line_item == str(row.get("line_item", "")),
                    CashFlowLine.period == str(row.get("period", "")),
                ).all()

                for line in lines:
                    line.actual_amount = float(actual)
                    line.source = CashFlowSource.accounting_system
                    count += 1

            log.status = "success"
            log.records_loaded = count
            log.message = f"Loaded {count} records from {file_path}"
            db.commit()
            return log
        except Exception as exc:
            log.status = "error"
            log.message = str(exc)
            db.commit()
            return log
