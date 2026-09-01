from __future__ import annotations

from pathlib import Path

import pandas as pd


class MasterWorkbook:
    """
    Loads and provides access to the Master Excel workbook.

    The workbook is expected to contain these validation sheets:

    - Student Marks
    - Section Avg by Subject
    - Chapter Avg by Section
    - Question Perf by Section
    - Score Distribution
    - Data_Chapter
    """

    REQUIRED_SHEETS = [
        "Student Marks",
        "Section Avg by Subject",
        "Chapter Avg by Section",
        "Question Perf by Section",
        "Score Distribution",
        "Data_Chapter",
    ]

    def __init__(self, path: str | Path):

        self.path = Path(path)

        if not self.path.exists():
            raise FileNotFoundError(
                f"Master Excel not found: {self.path}"
            )

        self._sheets: dict[str, pd.DataFrame] = {}

        self._load()

    # =========================================================
    # LOAD WORKBOOK
    # =========================================================

    def _load(self) -> None:

        print(
            f"Loading Master Excel: {self.path.name}"
        )

        excel = pd.ExcelFile(self.path)

        available_sheets = excel.sheet_names

        missing = [
            sheet
            for sheet in self.REQUIRED_SHEETS
            if sheet not in available_sheets
        ]

        if missing:

            raise RuntimeError(
                "Master Excel is missing required "
                f"sheet(s): {missing}"
            )

        for sheet_name in self.REQUIRED_SHEETS:

            df = pd.read_excel(
                self.path,
                sheet_name=sheet_name,
                header=3,
            )

            # Remove completely empty rows.
            df = df.dropna(
                how="all"
            ).reset_index(
                drop=True
            )

            # Clean column names.
            df.columns = [
                str(column).strip()
                for column in df.columns
            ]

            self._sheets[sheet_name] = df

        print(
            "✓ Master Excel loaded"
        )

    # =========================================================
    # GET SHEET
    # =========================================================

    def sheet(
        self,
        sheet_name: str,
    ) -> pd.DataFrame:

        if sheet_name not in self._sheets:

            raise KeyError(
                f"Sheet not loaded: {sheet_name}"
            )

        return self._sheets[sheet_name].copy()

    # =========================================================
    # VALIDATION SHEETS
    # =========================================================

    def student_marks(self) -> pd.DataFrame:

        return self.sheet(
            "Student Marks"
        )

    def section_avg_by_subject(
        self,
    ) -> pd.DataFrame:

        return self.sheet(
            "Section Avg by Subject"
        )

    def chapter_avg_by_section(
        self,
    ) -> pd.DataFrame:

        return self.sheet(
            "Chapter Avg by Section"
        )

    def question_perf_by_section(
        self,
    ) -> pd.DataFrame:

        return self.sheet(
            "Question Perf by Section"
        )

    def score_distribution(
        self,
    ) -> pd.DataFrame:

        return self.sheet(
            "Score Distribution"
        )

    def data_chapter(self) -> pd.DataFrame:

        return self.sheet(
            "Data_Chapter"
        )

    # =========================================================
    # BASIC INFORMATION
    # =========================================================

    @property
    def sheets(self) -> list[str]:

        return list(
            self._sheets.keys()
        )

    def __repr__(self) -> str:

        return (
            f"MasterWorkbook("
            f"path={self.path!s}, "
            f"sheets={self.sheets!r}"
            f")"
        )