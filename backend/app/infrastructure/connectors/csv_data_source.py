from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "scenario_id",
    "construction_object_id",
    "form_code",
    "line_item",
    "period",
    "actual_amount",
}


class CsvDataSource:
    def validate(self, file_path: str | Path) -> tuple[bool, list[str]]:
        path = Path(file_path)
        if not path.exists():
            return False, ["file does not exist"]
        frame = pd.read_csv(path)
        missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
        return not missing, missing

    def read(self, file_path: str | Path):
        return pd.read_csv(Path(file_path)).to_dict(orient="records")
