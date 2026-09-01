from __future__ import annotations

import re
from typing import Any

import pandas as pd


TOLERANCE = 0.9


# ============================================================
# HELPERS
# ============================================================

def _clean(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""

    return str(value).strip().upper()


def _number(value: Any) -> float | None:
    """
    Extract the first numeric value.

    Examples:
        16.4          -> 16.4
        "16.4 (47%)"  -> 16.4
        "0.83 (83%)"  -> 0.83
    """

    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if not match:
        return None

    return float(match.group())


def _percentage_from_display(
    value: Any,
) -> float | None:
    """
    Extract percentage from Display.

    Examples:
        "16.4 (47%)" -> 47
        "0.83 (83%)"  -> 83
        "92.1%"       -> 92.1
    """

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    # First try percentage inside parentheses.
    match = re.search(
        r"\(([-+]?\d+(?:\.\d+)?)\s*%\)",
        text,
    )

    if match:
        return float(match.group(1))

    # Otherwise look for any percentage.
    match = re.search(
        r"([-+]?\d+(?:\.\d+)?)\s*%",
        text,
    )

    if match:
        return float(match.group(1))

    return None


def _compare(
    api_value: Any,
    excel_value: Any,
    tolerance: float = TOLERANCE,
) -> dict:

    api_number = _number(api_value)
    excel_number = _number(excel_value)

    if api_number is None or excel_number is None:
        return {
            "status": "ERROR",
            "api_value": api_value,
            "excel_value": excel_value,
            "difference": None,
            "message": "Could not read numeric value.",
        }

    difference = abs(
        api_number - excel_number
    )

    return {
        "status": (
            "PASS"
            if difference <= tolerance
            else "FAIL"
        ),
        "api_value": api_number,
        "excel_value": excel_number,
        "difference": round(
            difference,
            3,
        ),
        "message": (
            "Within tolerance"
            if difference <= tolerance
            else "Outside tolerance"
        ),
    }


# ============================================================
# 1. INDIVIDUAL STUDENT MARKS
# ============================================================

def check_student_marks(
    roster: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
    tolerance: float = TOLERANCE,
) -> list[dict]:

    results = []

    for student in roster:

        roll = _clean(
            student.get("rollNumber")
        )

        api_marks = student.get(
            "totalMarks"
        )

        matches = master_df[
            master_df["Subject"].apply(_clean)
            == _clean(subject)
        ]

        matches = matches[
            matches["Section"].apply(_clean)
            == _clean(section)
        ]

        matches = matches[
            matches["Roll No"].apply(_clean)
            == roll
        ]

        if matches.empty:

            results.append({
                "check": "Individual Student Marks",
                "roll_number": roll,
                "student_name": student.get(
                    "studentName"
                ),
                "status": "MISSING",
                "api_value": api_marks,
                "excel_value": None,
                "difference": None,
                "message": (
                    "Student not found."
                ),
            })

            continue

        excel_display = matches.iloc[0][
            "Display"
        ]

        excel_marks = _number(
            excel_display
        )

        comparison = _compare(
            api_marks,
            excel_marks,
            tolerance,
        )

        results.append({
            "check": "Individual Student Marks",
            "roll_number": roll,
            "student_name": student.get(
                "studentName"
            ),
            **comparison,
        })

    return results


# ============================================================
# 2. SECTION AVERAGE
# ============================================================

def calculate_section_average(
    roster: list[dict],
) -> float:

    marks = []

    for student in roster:

        value = _number(
            student.get("totalMarks")
        )

        if value is not None:
            marks.append(value)

    if not marks:
        raise RuntimeError(
            "No student marks available."
        )

    return sum(marks) / len(marks)


def check_section_average(
    roster: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
    tolerance: float = TOLERANCE,
) -> dict:

    # Calculate from student-level API data.
    api_average = calculate_section_average(
        roster
    )

    matches = master_df[
        master_df["Subject"].apply(_clean)
        == _clean(subject)
    ]

    matches = matches[
        matches["Section"].apply(_clean)
        == _clean(section)
    ]

    if matches.empty:

        return {
            "check": "Section Average",
            "status": "MISSING",
            "api_value": api_average,
            "excel_value": None,
            "difference": None,
            "message": (
                "Subject + Section not found."
            ),
        }

    # Excel Display is like:
    # "16.4 (47%)"
    excel_average = _number(
        matches.iloc[0]["Display"]
    )

    return {
        "check": "Section Average",
        **_compare(
            api_average,
            excel_average,
            tolerance,
        ),
    }


# ============================================================
# 3. CHAPTER-WISE SECTION AVERAGE
# ============================================================

def check_chapter_average(
    chapter_stats: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
    tolerance: float = TOLERANCE,
) -> list[dict]:

    results = []

    for item in chapter_stats:

        chapter = item.get(
            "chapter"
        )

        api_value = item.get(
            "avgPct"
        )

        matches = master_df[
            master_df["Subject"].apply(_clean)
            == _clean(subject)
        ]

        matches = matches[
            matches["Section"].apply(_clean)
            == _clean(section)
        ]

        matches = matches[
            matches["Chapter"].apply(_clean)
            == _clean(chapter)
        ]

        if matches.empty:

            results.append({
                "check": "Chapter-wise Section Average",
                "chapter": chapter,
                "status": "MISSING",
                "api_value": api_value,
                "excel_value": None,
                "difference": None,
                "message": (
                    "Chapter not found."
                ),
            })

            continue

        excel_display = matches.iloc[0][
            "Display"
        ]

        # API avgPct = percentage.
        # Excel Display contains percentage
        # inside "(xx%)".
        excel_value = _percentage_from_display(
            excel_display
        )

        results.append({
            "check": "Chapter-wise Section Average",
            "chapter": chapter,
            **_compare(
                api_value,
                excel_value,
                tolerance,
            ),
        })

    return results


# ============================================================
# 4. SCORE DISTRIBUTION
# ============================================================

SCORE_BUCKETS = [
    "0-20%",
    "20-30%",
    "30-40%",
    "40-50%",
    "50-60%",
    "60-70%",
    "70-80%",
    "80-90%",
    "90-100%",
]


def calculate_score_distribution(
    roster: list[dict],
) -> dict:

    distribution = {
        bucket: 0
        for bucket in SCORE_BUCKETS
    }

    for student in roster:

        marks = _number(
            student.get("totalMarks")
        )

        max_marks = _number(
            student.get("totalMaxMarks")
        )

        if (
            marks is None
            or max_marks is None
            or max_marks == 0
        ):
            continue

        percentage = (
            marks / max_marks
        ) * 100

        # IMPORTANT:
        # Same boundaries as Master Excel.
        #
        # lower-inclusive
        # upper-exclusive
        # 90-100 includes >=90

        if percentage < 20:
            bucket = "0-20%"

        elif percentage < 30:
            bucket = "20-30%"

        elif percentage < 40:
            bucket = "30-40%"

        elif percentage < 50:
            bucket = "40-50%"

        elif percentage < 60:
            bucket = "50-60%"

        elif percentage < 70:
            bucket = "60-70%"

        elif percentage < 80:
            bucket = "70-80%"

        elif percentage < 90:
            bucket = "80-90%"

        else:
            bucket = "90-100%"

        distribution[bucket] += 1

    return distribution


def check_score_distribution(
    roster: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
) -> list[dict]:
    """
    Score Distribution has NO Display column.

    Excel structure:

        Subject block
            Section
            Students
            0-20%
            20-30%
            ...
            90-100%

    We calculate the same buckets from roster
    and compare each count directly.
    """

    api_distribution = (
        calculate_score_distribution(
            roster
        )
    )

    # Find the correct subject block.

    # The workbook has subject headings before
    # the actual distribution table.
    #
    # The section rows themselves contain the
    # section letter, so first identify rows
    # containing this section.

    section_matches = master_df[
        master_df["Section"].apply(_clean)
        == _clean(section)
    ]

    if section_matches.empty:

        return [{
            "check": "Student Score Distribution",
            "status": "MISSING",
            "api_value": api_distribution,
            "excel_value": None,
            "difference": None,
            "message": (
                "Section not found in Score Distribution."
            ),
        }]

    # Since Score Distribution contains blocks
    # for multiple subjects, we need to ensure
    # the selected subject's block is being used.
    #
    # The loader will provide Subject when the
    # sheet is parsed. If Subject isn't present
    # in this special sheet, the matching section
    # row is used.

    row = section_matches.iloc[0]

    results = []

    for bucket in SCORE_BUCKETS:

        if bucket not in row.index:

            results.append({
                "check": "Student Score Distribution",
                "range": bucket,
                "status": "ERROR",
                "api_value": api_distribution[bucket],
                "excel_value": None,
                "difference": None,
                "message": (
                    f"Column '{bucket}' not found."
                ),
            })

            continue

        excel_count = _number(
            row[bucket]
        )

        api_count = api_distribution[
            bucket
        ]

        results.append({
            "check": "Student Score Distribution",
            "range": bucket,
            **_compare(
                api_count,
                excel_count,
                0,
            ),
        })

    return results


# ============================================================
# 5. QUESTION-WISE AVERAGE
# ============================================================

def check_question_stats(
    question_stats: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
    tolerance: float = TOLERANCE,
) -> list[dict]:

    results = []

    for question in question_stats:

        q_number = question.get(
            "questionNumber"
        )

        api_accuracy = question.get(
            "accuracy"
        )

        matches = master_df[
            master_df["Subject"].apply(_clean)
            == _clean(subject)
        ]

        matches = matches[
            matches["Section"].apply(_clean)
            == _clean(section)
        ]

        matches = matches[
            pd.to_numeric(
                matches["Q No"],
                errors="coerce",
            )
            == float(q_number)
        ]

        if matches.empty:

            results.append({
                "check": "Question-wise Average",
                "question": q_number,
                "status": "MISSING",
                "api_value": api_accuracy,
                "excel_value": None,
                "difference": None,
                "message": (
                    "Question not found."
                ),
            })

            continue

        excel_display = matches.iloc[0][
            "Display"
        ]

        # API accuracy = percentage.
        #
        # Excel:
        # "0.83 (83%)"
        #
        # We therefore compare:
        # API 83 ↔ Excel 83

        excel_accuracy = (
            _percentage_from_display(
                excel_display
            )
        )

        results.append({
            "check": "Question-wise Average",
            "question": q_number,
            **_compare(
                api_accuracy,
                excel_accuracy,
                tolerance,
            ),
        })

    return results


# ============================================================
# 6. STUDENT CHAPTER-WISE AVERAGE
# ============================================================

def check_student_chapter_stats(
    student_chapter_stats: list[dict],
    master_df: pd.DataFrame,
    subject: str,
    section: str,
    tolerance: float = TOLERANCE,
) -> list[dict]:

    results = []

    for record in student_chapter_stats:

        roll = _clean(
            record.get("rollNumber")
        )

        chapter = record.get(
            "chapter"
        )

        api_got = record.get(
            "got"
        )

        matches = master_df[
            master_df["Subject"].apply(_clean)
            == _clean(subject)
        ]

        matches = matches[
            matches["Section"].apply(_clean)
            == _clean(section)
        ]

        matches = matches[
            matches["Roll No"].apply(_clean)
            == roll
        ]

        matches = matches[
            matches["Chapter"].apply(_clean)
            == _clean(chapter)
        ]

        if matches.empty:

            results.append({
                "check": (
                    "Student Chapter-wise Average"
                ),
                "roll_number": roll,
                "chapter": chapter,
                "status": "MISSING",
                "api_value": api_got,
                "excel_value": None,
                "difference": None,
                "message": (
                    "Student + Chapter not found."
                ),
            })

            continue

        excel_display = matches.iloc[0][
            "Display"
        ]

        # API `got` is marks.
        #
        # Excel Display:
        # "10. (56%)"
        #
        # Therefore compare 10 ↔ 10.

        excel_got = _number(
            excel_display
        )

        results.append({
            "check": (
                "Student Chapter-wise Average"
            ),
            "roll_number": roll,
            "chapter": chapter,
            **_compare(
                api_got,
                excel_got,
                tolerance,
            ),
        })

    return results


# ============================================================
# SUMMARY
# ============================================================

def summarize_results(
    results: list[dict],
) -> dict:

    total = len(results)

    passed = sum(
        1
        for result in results
        if result.get("status") == "PASS"
    )

    failed = sum(
        1
        for result in results
        if result.get("status") == "FAIL"
    )

    missing = sum(
        1
        for result in results
        if result.get("status") == "MISSING"
    )

    errors = sum(
        1
        for result in results
        if result.get("status") == "ERROR"
    )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "missing": missing,
        "errors": errors,
        "pass_rate": (
            round(
                passed / total * 100,
                2,
            )
            if total
            else 0
        ),
    }