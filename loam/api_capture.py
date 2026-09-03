


from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import Response

EXAM_API_IDS = {
    # UNIT TEST-1--------------------------------------------------------------------------------------
    # Class 11
    ("11", "Accountancy", "Unit Test 1 2026-27"): "11_ACCOUNTANCY_Unit-Test -1_26_27",
    ("11", "Applied Mathematics", "Unit Test 1 2026-27"):"11_Applied_Mathematics_Unit-Test -1_26_27",
    ("11", "Biology", "Unit Test 1 2026-27"):"11_Biology_Unit-Test -1_26_27",
    ("11", "Chemistry", "Unit Test 1 2026-27"):"11_Chemistry_Unit-Test -1_26_27",
    ("11", "Economics", "Unit Test 1 2026-27"):"11_Economics_Unit-Test -1_26_27",
    ("11", "Mathematics", "Unit Test 1 2026-27"):"11_Mathematics_Unit-Test -1_26_27",
    ("11", "Physics", "Unit Test 1 2026-27"): "11_Physics_Unit-Test -1_26_27",
    ("11", "Science", "Unit Test 1 2026-27"): "11_Science_Unit-Test -1_26_27",
    ("11", "Social Science", "Unit Test 1 2026-27"):"11_Social+Science_Unit-Test -1_26_27",

    #CLASS 10
    ("10", "Mathematics", "Unit Test 1 2026-27"): "10_MATHEMATICS_Unit-Test -1_26_27",
    ("10", "Science", "Unit Test 1 2026-27"): "10_SCIENCE_Unit-Test -1_26_27",
    ("10", "Social Science", "Unit Test 1 2026-27"): "10_Social+Science_Unit-Test -1_26_27",

    #CLASS 9
    ("9", "Mathematics", "Unit Test 1 2026-27"): "9_Mathematics_Unit-Test -1_26_27",
    ("9", "Science", "Unit Test 1 2026-27"): "9_Science_Unit-Test -1_26_27",
    ("9", "Social Science", "Unit Test 1 2026-27"): "9_Social+Science_Unit-Test -1_26_27",

    #CLASS 12
    ("12", "Accountancy", "Unit Test 1 2026-27"): "12_ACCOUNTANCY_Unit-Test -1_26_27",
    ("12", "Applied Mathematics", "Unit Test 1 2026-27"):"12_Applied_Mathematics_Unit-Test -1_26_27",
    ("12", "Biology", "Unit Test 1 2026-27"):"12_Biology_Unit-Test -1_26_27",
    ("12", "Chemistry", "Unit Test 1 2026-27"):"12_Chemistry_Unit-Test -1_26_27",
    ("12", "Economics", "Unit Test 1 2026-27"):"12_Economics_Unit-Test -1_26_27",
    ("12", "Mathematics", "Unit Test 1 2026-27"):"12_Mathematics_Unit-Test -1_26_27",
    ("12", "Physics", "Unit Test 1 2026-27"): "12_Physics_Unit-Test -1_26_27",
    ("12", "Science", "Unit Test 1 2026-27"): "12_Science_Unit-Test -1_26_27",
    ("12", "Social Science", "Unit Test 1 2026-27"):"12_Social+Science_Unit-Test -1_26_27",


}


CHAPTER_STATS_PATH = "/api/answer-crops/chapter-stats"
ROSTER_PATH = "/api/answer-crops/roster"
STUDENT_CHAPTER_STATS_PATH = "/api/answer-crops/student-chapter-stats"
QUESTION_STATS_PATH = "/api/answer-crops/question-stats"
QUESTIONS_PATH = "/api/questions"


class ApiCollector:
    def __init__(self) -> None:
        self.capture_enabled = False

        self.chapter_stats: Any | None = None
        self.roster: Any | None = None
        self.student_chapter_stats: Any | None = None
        self.question_stats: Any | None = None
        self.questions: Any | None = None

        self.captured_urls: list[str] = []

        # Actual API exam identifier.
        self.expected_exam_id: str | None = None

        # Keep responses until we know which exam they belong to.

    def set_exam(
        self,
        grade: str,
        subject: str,
        exam: str,
    ) -> None:

        key = (
            str(grade).strip(),
            str(subject).strip(),
            str(exam).strip(),
        )

        self.expected_exam_id = EXAM_API_IDS.get(key)

        if not self.expected_exam_id:
            raise ValueError(
                f"No API exam ID configured for: "
                f"{grade} / {subject} / {exam}"
            )

        print(
            f"✓ API exam ID → {self.expected_exam_id}"
        )

    def clear(self):
        self.chapter_stats = None
        self.roster = None
        self.student_chapter_stats = None
        self.question_stats = None
        self.questions = None

        self.captured_urls = []

        # Keep expected_exam_id.
        # It belongs to the selected exam for this script run.



    def enable(self) -> None:
        self.capture_enabled = True

    def disable(self) -> None:
        self.capture_enabled = False

    @staticmethod
    def get_exam_id(url: str) -> str | None:
        try:
            query = parse_qs(
                urlparse(url).query
            )

            exam_values = query.get("exam")

            if not exam_values:
                return None

            return unquote(exam_values[0])

        except Exception:
            return None


    def handle_response(self, response):
        if not self.capture_enabled:
            return

        if response.status != 200:
            return

        url = response.url
        parsed = urlparse(url)
        path = parsed.path

        allowed_paths = {
            CHAPTER_STATS_PATH,
            ROSTER_PATH,
            STUDENT_CHAPTER_STATS_PATH,
            QUESTION_STATS_PATH,
            QUESTIONS_PATH,
        }

        if path not in allowed_paths:
            return

        exam_id = self.get_exam_id(url)

        # These APIs are exam-specific.
        exam_scoped_paths = {
            ROSTER_PATH,
            STUDENT_CHAPTER_STATS_PATH,
            QUESTION_STATS_PATH,
        }

        if path in exam_scoped_paths:
            if exam_id != self.expected_exam_id:
                print(
                    f"  ↳ Ignored {path.split('/')[-1]} "
                    f"(exam={exam_id})"
                )
                return

        try:
            data = response.json()
        except Exception:
            return

        self.captured_urls.append(url)

        if path == CHAPTER_STATS_PATH:
            self.chapter_stats = data

        elif path == ROSTER_PATH:
            self.roster = data

        elif path == STUDENT_CHAPTER_STATS_PATH:
            self.student_chapter_stats = data

        elif path == QUESTION_STATS_PATH:
            self.question_stats = data

        elif path == QUESTIONS_PATH:
            self.questions = data

    def get_roster(self):

        if self.roster is None:
            raise RuntimeError(
                "Roster API was not captured."
            )

        return self.roster

    def get_student_chapter_stats(self):

        if self.student_chapter_stats is None:
            raise RuntimeError(
                "Student chapter stats API was not captured."
            )

        return self.student_chapter_stats

    def get_question_stats(self):

        if self.question_stats is None:
            raise RuntimeError(
                "Question stats API was not captured."
            )

        return self.question_stats

    def get_questions(self):
        if self.questions is None:
            raise RuntimeError(
                "/api/questions API was not captured."
            )

        return self.questions

    def missing_apis(self) -> list[str]:
        missing = []

        if self.chapter_stats is None:
            missing.append("chapter-stats")

        if self.roster is None:
            missing.append("roster")

        if self.student_chapter_stats is None:
            missing.append("student-chapter-stats")

        if self.question_stats is None:
            missing.append("question-stats")

        if self.questions is None:
            missing.append("questions")

        return missing

    def all_required_apis_captured(self) -> bool:
        return len(
            self.missing_apis()
        ) == 0