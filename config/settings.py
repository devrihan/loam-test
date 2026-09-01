from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """
    Central configuration for the LOAM data validation automation.
    """

    # ---------------------------------------------------------
    # LOAM
    # ---------------------------------------------------------

    base_url = os.getenv(
        "LOAM_BASE_URL",
        "https://dps.inferentics.com/login",
    )

    username = os.getenv("LOAM_USERNAME")
    password = os.getenv("LOAM_PASSWORD")

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    # Difference allowed between LOAM/API and Master Excel.
    #
    # For percentage values:
    #   92.1 vs 92.0 -> difference = 0.1 percentage points
    #
    # For marks:
    #   16.0 vs 16.5 -> difference = 0.5 marks
    #
    # Both are accepted because they are <= 0.9.
    numeric_tolerance = 0.9

    # ---------------------------------------------------------
    # Master Excel files
    # ---------------------------------------------------------

    MASTER_FILES = {
        "9": PROJECT_ROOT
        / "master_data"
        / "Class9_UnitTest1_Analysis_202627.xlsx",

        "10": PROJECT_ROOT
        / "master_data"
        / "Class10_UnitTest1_Analysis_202627.xlsx",

        "11": PROJECT_ROOT
        / "master_data"
        / "Class11_UnitTest1_Analysis_202627.xlsx",

        "12": PROJECT_ROOT
        / "master_data"
        / "Class12_UnitTest1_Analysis_202627.xlsx",
    }

    @classmethod
    def master_file_for_grade(cls, grade: str) -> Path:
        """
        Return the Master Excel corresponding to a grade.
        """

        grade = str(grade).strip()

        if grade not in cls.MASTER_FILES:
            raise RuntimeError(
                f"No Master Excel configured for Grade {grade}"
            )

        path = cls.MASTER_FILES[grade]

        if not path.exists():
            raise FileNotFoundError(
                f"Master Excel not found for Grade {grade}: {path}"
            )

        return path