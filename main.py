from __future__ import annotations

import argparse
import json

from playwright.sync_api import sync_playwright

from config.settings import Settings
from loam.navigator import LoamNavigator
from loam.api_capture import ApiCollector
from master.excel_loader import MasterWorkbook

from validation.checks import (
    check_student_marks,
    check_section_average,
    check_chapter_average,
    check_question_stats,
    check_student_chapter_stats,
    summarize_results,
)

from report.html_report import write_and_open_report


# ============================================================
# PRINT CHECK SUMMARY
# ============================================================

def print_check_summary(
    name: str,
    results: list[dict],
) -> None:

    summary = summarize_results(results)

    print(f"\n{name}")
    print("-" * 60)

    print(
        f"Total: {summary['total']} | "
        f"PASS: {summary['passed']} | "
        f"FAIL: {summary['failed']} | "
        f"MISSING: {summary['missing']} | "
        f"ERROR: {summary['errors']}"
    )

    print(
        f"Pass Rate: {summary['pass_rate']}%"
    )


# ============================================================
# PRINT FAILURES
# ============================================================

def print_failures(
    check_name: str,
    results: list[dict],
) -> None:

    failures = [
        result
        for result in results
        if result.get("status") in {
            "FAIL",
            "MISSING",
            "ERROR",
        }
    ]

    if not failures:
        return

    print(
        f"\n{'!' * 70}"
    )

    print(
        f"MISMATCHES — {check_name}"
    )

    print(
        f"{'!' * 70}"
    )

    for result in failures:

        print()

        if "roll_number" in result:
            print(
                f"Roll No       : "
                f"{result.get('roll_number')}"
            )

        if result.get("student_name"):
            print(
                f"Student       : "
                f"{result.get('student_name')}"
            )

        if "chapter" in result:
            print(
                f"Chapter       : "
                f"{result.get('chapter')}"
            )

        if "question" in result:
            print(
                f"Question      : "
                f"{result.get('question')}"
            )

        if "range" in result:
            print(
                f"Range         : "
                f"{result.get('range')}"
            )

        print(
            f"API Value     : "
            f"{result.get('api_value')}"
        )

        print(
            f"Excel Value   : "
            f"{result.get('excel_value')}"
        )

        print(
            f"Difference    : "
            f"{result.get('difference')}"
        )

        print(
            f"Status        : "
            f"{result.get('status')}"
        )

        if result.get("message"):
            print(
                f"Message       : "
                f"{result.get('message')}"
            )

        print(
            "-" * 50
        )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--master",
        required=True,
        help="Path to Master Excel file",
    )

    parser.add_argument(
        "--subject",
        default="Accountancy",
        help="Subject to test",
    )

    parser.add_argument(
        "--grade-section",
        default="12-C",
        help="Grade-Section to test",
    )

    args = parser.parse_args()

    settings = Settings()

    if not settings.username:
        raise RuntimeError(
            "LOAM_USERNAME is missing from .env"
        )

    if not settings.password:
        raise RuntimeError(
            "LOAM_PASSWORD is missing from .env"
        )

    # ========================================================
    # PARSE GRADE / SECTION
    # ========================================================

    try:

        grade, section = (
            args.grade_section.split(
                "-",
                1,
            )
        )

    except ValueError:

        raise RuntimeError(
            "Grade-Section must look like 12-C"
        )

    # ========================================================
    # HEADER
    # ========================================================

    print("=" * 70)

    print(
        "LOAM DATA VALIDATION"
    )

    print("=" * 70)

    print(
        f"Subject       : {args.subject}"
    )

    print(
        f"Grade-Section : "
        f"{args.grade_section}"
    )

    print(
        f"Master Excel  : "
        f"{args.master}"
    )

    print(
        f"Tolerance     : "
        f"{settings.numeric_tolerance}"
    )

    print("=" * 70)

    # ========================================================
    # LOAD MASTER EXCEL
    # ========================================================

    print(
        f"\nLoading Master Excel: "
        f"{args.master}"
    )

    master = MasterWorkbook(
        args.master
    )

    print(
        "✓ Master Excel loaded"
    )

    # ========================================================
    # PLAYWRIGHT
    # ========================================================

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context()

        page = context.new_page()

        # ----------------------------------------------------
        # API COLLECTOR
        # ----------------------------------------------------

        collector = ApiCollector()

        page.on(
            "response",
            collector.handle_response,
        )

        # ----------------------------------------------------
        # NAVIGATOR
        # ----------------------------------------------------

        nav = LoamNavigator(
            page=page,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password,
        )

        # ====================================================
        # 1. LOGIN
        # ====================================================

        print("\n[1] LOGIN")

        nav.login()

        # ====================================================
        # 2. SUBJECT
        # ====================================================

        print("\n[2] SUBJECT")

        nav.select_subject(
            args.subject
        )

        # ====================================================
        # 3. GRADE SECTION
        # ====================================================

        print("\n[3] GRADE-SECTION")

        nav.select_grade_section(
            args.grade_section
        )

        # ====================================================
        # 4. CHAPTER
        # ====================================================

        print("\n[4] CHAPTER")

        # IMPORTANT:
        # The chapter-stats API must be captured after
        # actually opening the Chapter tab.

        nav.go_to_chapter()

        # Give the Chapter page/API time to load.

        page.wait_for_timeout(
            3000
        )

        chapter_stats = (
            collector.get_chapter_stats()
        )

        if chapter_stats is None:

            raise RuntimeError(
                "chapter-stats API was not captured "
                "after opening Chapter tab."
            )

        print(
            "✓ chapter-stats API captured"
        )

        # ====================================================
        # 5. STUDENTS
        # ====================================================

        print("\n[5] STUDENTS")

        nav.go_to_students()

        page.wait_for_timeout(
            3000
        )

        roster = (
            collector.get_roster()
        )

        student_chapter_stats = (
            collector.get_student_chapter_stats()
        )

        if roster is None:

            raise RuntimeError(
                "roster API was not captured."
            )

        if student_chapter_stats is None:

            raise RuntimeError(
                "student-chapter-stats API "
                "was not captured."
            )

        print(
            "✓ roster API captured"
        )

        print(
            "✓ student-chapter-stats API captured"
        )

        # ====================================================
        # 6. QUESTIONS
        # ====================================================

        print("\n[6] QUESTIONS")

        nav.go_to_questions()

        page.wait_for_timeout(
            3000
        )

        question_stats = (
            collector.get_question_stats()
        )

        if question_stats is None:

            raise RuntimeError(
                "question-stats API was not captured."
            )

        print(
            "✓ question-stats API captured"
        )

        # ====================================================
        # 7. VERIFY API CAPTURE
        # ====================================================

        print("\n[7] API CAPTURE")

        missing = collector.missing_apis()

        if missing:

            print(
                "⚠ Missing API responses:"
            )

            for api in missing:

                print(
                    f"  - {api}"
                )

            raise RuntimeError(
                "Not all required APIs were captured."
            )

        print(
            "✓ All four required APIs captured"
        )

        # ====================================================
        # 8. API DATA
        # ====================================================

        print("\n[8] API DATA")

        print(
            f"Students              : "
            f"{len(roster)}"
        )

        print(
            f"Chapters              : "
            f"{len(chapter_stats)}"
        )

        print(
            f"Student-Chapter rows  : "
            f"{len(student_chapter_stats)}"
        )

        print(
            f"Questions             : "
            f"{len(question_stats)}"
        )

        # ====================================================
        # 9. VALIDATION
        # ====================================================

        print("\n[9] VALIDATION")

        all_results = {}

        # ====================================================
        # CHECK 1
        # Individual Student Marks
        # ====================================================

        student_marks_results = (
            check_student_marks(
                roster=roster,
                master_df=master.student_marks(),
                subject=args.subject,
                section=section,
                tolerance=settings.numeric_tolerance,
            )
        )

        all_results[
            "Individual Student Marks"
        ] = student_marks_results

        print_check_summary(
            "1. Individual Student Marks",
            student_marks_results,
        )

        print_failures(
            "1. Individual Student Marks",
            student_marks_results,
        )

        # ====================================================
        # CHECK 2
        # Section Average
        # ====================================================

        section_average_result = (
            check_section_average(
                roster=roster,
                master_df=master.section_avg_by_subject(),
                subject=args.subject,
                section=section,
                tolerance=settings.numeric_tolerance,
            )
        )

        # check_section_average returns ONE dict.

        all_results[
            "Section Average"
        ] = [
            section_average_result
        ]

        print_check_summary(
            "2. Section Average",
            [section_average_result],
        )

        print_failures(
            "2. Section Average",
            [section_average_result],
        )

        # ====================================================
        # CHECK 3
        # Chapter-wise Section Average
        # ====================================================

        chapter_average_results = (
            check_chapter_average(
                chapter_stats=chapter_stats,
                master_df=master.chapter_avg_by_section(),
                subject=args.subject,
                section=section,
                tolerance=settings.numeric_tolerance,
            )
        )

        all_results[
            "Chapter-wise Section Average"
        ] = chapter_average_results

        print_check_summary(
            "3. Chapter-wise Section Average",
            chapter_average_results,
        )

        print_failures(
            "3. Chapter-wise Section Average",
            chapter_average_results,
        )

        # ====================================================
        # CHECK 5
        # Question-wise Average
        # ====================================================

        question_results = (
            check_question_stats(
                question_stats=question_stats,
                master_df=master.question_perf_by_section(),
                subject=args.subject,
                section=section,
                tolerance=settings.numeric_tolerance,
            )
        )

        all_results[
            "Question-wise Average"
        ] = question_results

        print_check_summary(
            "5. Question-wise Average",
            question_results,
        )

        print_failures(
            "5. Question-wise Average",
            question_results,
        )

        # ====================================================
        # CHECK 6
        # Student Chapter-wise Average
        # ====================================================

        student_chapter_results = (
            check_student_chapter_stats(
                student_chapter_stats=student_chapter_stats,
                master_df=master.data_chapter(),
                subject=args.subject,
                section=section,
                tolerance=settings.numeric_tolerance,
            )
        )

        all_results[
            "Student Chapter-wise Average"
        ] = student_chapter_results

        print_check_summary(
            "6. Student Chapter-wise Average",
            student_chapter_results,
        )

        print_failures(
            "6. Student Chapter-wise Average",
            student_chapter_results,
        )

        # ====================================================
        # 10. FINAL SUMMARY
        # ====================================================

        print("\n")

        print("=" * 70)

        print(
            "FINAL VALIDATION SUMMARY"
        )

        print("=" * 70)

        total_checks = 0
        total_pass = 0
        total_fail = 0
        total_missing = 0
        total_errors = 0

        for check_name, results in (
            all_results.items()
        ):

            summary = summarize_results(
                results
            )

            total_checks += (
                summary["total"]
            )

            total_pass += (
                summary["passed"]
            )

            total_fail += (
                summary["failed"]
            )

            total_missing += (
                summary["missing"]
            )

            total_errors += (
                summary["errors"]
            )

            print(
                f"{check_name:<35} "
                f"PASS={summary['passed']:<4} "
                f"FAIL={summary['failed']:<4} "
                f"MISSING={summary['missing']:<4}"
            )

        print(
            "-" * 70
        )

        print(
            f"TOTAL   : {total_checks}"
        )

        print(
            f"PASS    : {total_pass}"
        )

        print(
            f"FAIL    : {total_fail}"
        )

        print(
            f"MISSING : {total_missing}"
        )

        print(
            f"ERROR   : {total_errors}"
        )

        if total_checks:

            print(
                f"PASS RATE: "
                f"{round(total_pass / total_checks * 100, 2)}%"
            )

        # ====================================================
        # 11. SAVE JSON
        # ====================================================

        json_report_path = (
            "validation_result.json"
        )

        with open(
            json_report_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                {
                    "subject": args.subject,
                    "grade_section": args.grade_section,
                    "master_excel": args.master,
                    "tolerance": (
                        settings.numeric_tolerance
                    ),
                    "results": all_results,
                },
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"\n✓ Validation result saved to "
            f"{json_report_path}"
        )

        # ====================================================
        # 12. HTML TEST REPORT
        # ====================================================

        print(
            "\nGenerating HTML test report..."
        )

        html_report_path = (
            write_and_open_report(
                subject=args.subject,
                grade_section=args.grade_section,
                master_excel=args.master,
                tolerance=settings.numeric_tolerance,
                all_results=all_results,
            )
        )

        print(
            f"✓ Report generated: "
            f"{html_report_path}"
        )

        print(
            "✓ Report opened in your browser"
        )

        # Keep Playwright browser open briefly.

        page.wait_for_timeout(
            5000
        )

        browser.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()