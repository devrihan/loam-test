


from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import html

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


def _print_final_summary(all_results: dict[str, list[dict]]) -> dict:
    print("\n")
    print("=" * 70)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 70)

    total_checks = 0
    total_pass = 0
    total_fail = 0
    total_missing = 0
    total_errors = 0

    for check_name, results in all_results.items():
        summary = summarize_results(results)

        total_checks += summary["total"]
        total_pass += summary["passed"]
        total_fail += summary["failed"]
        total_missing += summary["missing"]
        total_errors += summary["errors"]

        print(
            f"{check_name:<35} "
            f"PASS={summary['passed']:<4} "
            f"FAIL={summary['failed']:<4} "
            f"MISSING={summary['missing']:<4}"
        )

    print("-" * 70)
    print(f"TOTAL   : {total_checks}")
    print(f"PASS    : {total_pass}")
    print(f"FAIL    : {total_fail}")
    print(f"MISSING : {total_missing}")
    print(f"ERROR   : {total_errors}")

    pass_rate = (
        round(total_pass / total_checks * 100, 2)
        if total_checks
        else 0
    )
    print(f"PASS RATE: {pass_rate}%")

    return {
        "total": total_checks,
        "passed": total_pass,
        "failed": total_fail,
        "missing": total_missing,
        "errors": total_errors,
        "pass_rate": pass_rate,
    }


def _save_json_report(
    *,
    path: str,
    subject: str,
    grade_section: str,
    master_excel: str,
    tolerance: float,
    all_results: dict[str, list[dict]],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "subject": subject,
                "grade_section": grade_section,
                "master_excel": master_excel,
                "tolerance": tolerance,
                "results": all_results,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )


def validate_one(
    *,
    master: MasterWorkbook,
    subject: str,
    grade_section: str,
    settings: Settings,
    nav: LoamNavigator,
    page,
    collector: ApiCollector,
    open_report: bool = True,
    report_path: str | None = None,
    json_path: str | None = None,
) -> tuple[dict[str, list[dict]], dict]:
    """Run the existing five checks for one subject + grade-section."""

    try:
        grade, section = grade_section.split("-", 1)
    except ValueError:
        raise RuntimeError(
            f"Grade-Section must look like 11-C, got: {grade_section}"
        )

    # Prevent API responses from a previous combination from being reused.
    collector.clear()

    print("\n" + "=" * 70)
    print("VALIDATING")
    print("=" * 70)
    print(f"Subject       : {subject}")
    print(f"Grade-Section : {grade_section}")
    print(f"Master Excel  : {master.path if hasattr(master, 'path') else 'selected workbook'}")
    print("=" * 70)

    # ========================================================
    # SUBJECT
    # ========================================================
    print("\n[1] SUBJECT")
    nav.select_subject(subject)

    # ========================================================
    # GRADE SECTION
    # ========================================================
    print("\n[2] GRADE-SECTION")
    nav.select_grade_section(grade_section)

    # ========================================================
    # CHAPTER
    # ========================================================
    print("\n[3] CHAPTER")
    nav.go_to_chapter()
    page.wait_for_timeout(3000)

    chapter_stats = collector.get_chapter_stats()
    if chapter_stats is None:
        raise RuntimeError(
            "chapter-stats API was not captured after opening Chapter tab."
        )
    print("✓ chapter-stats API captured")

    # ========================================================
    # STUDENTS
    # ========================================================
    print("\n[4] STUDENTS")
    nav.go_to_students()
    page.wait_for_timeout(3000)

    roster = collector.get_roster()
    student_chapter_stats = collector.get_student_chapter_stats()

    if roster is None:
        raise RuntimeError("roster API was not captured.")
    if student_chapter_stats is None:
        raise RuntimeError("student-chapter-stats API was not captured.")

    print("✓ roster API captured")
    print("✓ student-chapter-stats API captured")

    # ========================================================
    # QUESTIONS
    # ========================================================
    print("\n[5] QUESTIONS")
    nav.go_to_questions()
    page.wait_for_timeout(3000)

    question_stats = collector.get_question_stats()
    if question_stats is None:
        raise RuntimeError("question-stats API was not captured.")

    print("✓ question-stats API captured")

    # ========================================================
    # API CAPTURE
    # ========================================================
    print("\n[6] API CAPTURE")
    missing = collector.missing_apis()

    if missing:
        print("⚠ Missing API responses:")
        for api in missing:
            print(f"  - {api}")
        raise RuntimeError("Not all required APIs were captured.")

    print("✓ All four required APIs captured")

    # ========================================================
    # API DATA
    # ========================================================
    print("\n[7] API DATA")
    print(f"Students              : {len(roster)}")
    print(f"Chapters              : {len(chapter_stats)}")
    print(f"Student-Chapter rows  : {len(student_chapter_stats)}")
    print(f"Questions             : {len(question_stats)}")

    # ========================================================
    # VALIDATION
    # ========================================================
    print("\n[8] VALIDATION")
    all_results = {}

    # 1. Individual Student Marks
    student_marks_results = check_student_marks(
        roster=roster,
        master_df=master.student_marks(),
        subject=subject,
        section=section,
        tolerance=settings.numeric_tolerance,
    )
    all_results["Individual Student Marks"] = student_marks_results
    print_check_summary("1. Individual Student Marks", student_marks_results)
    print_failures("1. Individual Student Marks", student_marks_results)

    # 2. Section Average
    section_average_result = check_section_average(
        roster=roster,
        master_df=master.section_avg_by_subject(),
        subject=subject,
        section=section,
        tolerance=settings.numeric_tolerance,
    )
    all_results["Section Average"] = [section_average_result]
    print_check_summary("2. Section Average", [section_average_result])
    print_failures("2. Section Average", [section_average_result])

    # 3. Chapter-wise Section Average
    chapter_average_results = check_chapter_average(
        chapter_stats=chapter_stats,
        master_df=master.chapter_avg_by_section(),
        subject=subject,
        section=section,
        tolerance=settings.numeric_tolerance,
    )
    all_results["Chapter-wise Section Average"] = chapter_average_results
    print_check_summary(
        "3. Chapter-wise Section Average",
        chapter_average_results,
    )
    print_failures(
        "3. Chapter-wise Section Average",
        chapter_average_results,
    )

    # 5. Question-wise Average
    question_results = check_question_stats(
        question_stats=question_stats,
        master_df=master.question_perf_by_section(),
        subject=subject,
        section=section,
        tolerance=settings.numeric_tolerance,
    )
    all_results["Question-wise Average"] = question_results
    print_check_summary("5. Question-wise Average", question_results)
    print_failures("5. Question-wise Average", question_results)

    # 6. Student Chapter-wise Average
    student_chapter_results = check_student_chapter_stats(
        student_chapter_stats=student_chapter_stats,
        master_df=master.data_chapter(),
        subject=subject,
        section=section,
        tolerance=settings.numeric_tolerance,
    )
    all_results["Student Chapter-wise Average"] = student_chapter_results
    print_check_summary(
        "6. Student Chapter-wise Average",
        student_chapter_results,
    )
    print_failures(
        "6. Student Chapter-wise Average",
        student_chapter_results,
    )

    summary = _print_final_summary(all_results)

    # ========================================================
    # SAVE JSON
    # ========================================================
    if json_path is None:
        json_path = "validation_result.json"

    _save_json_report(
        path=json_path,
        subject=subject,
        grade_section=grade_section,
        master_excel=str(getattr(master, "path", "")),
        tolerance=settings.numeric_tolerance,
        all_results=all_results,
    )
    print(f"\n✓ Validation result saved to {json_path}")

    # ========================================================
    # HTML REPORT
    # ========================================================
    if report_path is None:
        report_path = "reports/loam_validation_report.html"

    print("\nGenerating HTML test report...")

    # Existing report function also opens the report. In batch mode we suppress
    # this by generating the HTML directly when possible; single mode keeps the
    # original behavior.
    if open_report:
        html_report_path = write_and_open_report(
            subject=subject,
            grade_section=grade_section,
            master_excel=str(getattr(master, "path", "")),
            tolerance=settings.numeric_tolerance,
            all_results=all_results,
            output_path=report_path,
        )
    else:
        from report.html_report import build_html_report

        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(
            build_html_report(
                subject=subject,
                grade_section=grade_section,
                master_excel=str(getattr(master, "path", "")),
                tolerance=settings.numeric_tolerance,
                all_results=all_results,
            ),
            encoding="utf-8",
        )
        html_report_path = report_file

    print(f"✓ Report generated: {html_report_path}")

    return all_results, summary


def _extract_grade_from_filename(path: Path) -> str | None:
    match = re.search(r"class\s*(9|10|11|12)\b", path.stem, re.IGNORECASE)
    if match:
        return match.group(1)

    # Fallback for names such as 11_Accountancy_...
    match = re.search(r"(?<!\d)(9|10|11|12)(?!\d)", path.stem)
    return match.group(1) if match else None


def _build_batch_report(batch_results: list[dict], output_path: str) -> Path:
    """Create one dark, modern summary page for the entire batch."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    total = sum(item["summary"]["total"] for item in batch_results)
    passed = sum(item["summary"]["passed"] for item in batch_results)
    failed = sum(item["summary"]["failed"] for item in batch_results)
    missing = sum(item["summary"]["missing"] for item in batch_results)
    errors = sum(item["summary"]["errors"] for item in batch_results)
    rate = round(passed / total * 100, 2) if total else 0

    rows = []
    for item in batch_results:
        s = item["summary"]
        status = "PASS" if s["failed"] == 0 and s["errors"] == 0 and s["missing"] == 0 else "FAIL"
        cls = "pass" if status == "PASS" else "fail"
        report_link = Path(item["report"]).relative_to("reports").as_posix()
        rows.append(
            f"""
            <tr>
              <td>{html.escape(item["grade_section"])}</td>
              <td>{html.escape(item["subject"])}</td>
              <td>{s["total"]}</td>
              <td>{s["passed"]}</td>
              <td>{s["failed"]}</td>
              <td>{s["missing"]}</td>
              <td>{s["errors"]}</td>
              <td>{s["pass_rate"]}%</td>
              <td><span class="badge {cls}">{status}</span></td>
              <td><a href="{html.escape(report_link)}">View report</a></td>
            </tr>
            """
        )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>LOAM Batch Validation</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
  background: #07090d;
  color: #f5f7fb;
}}
.wrap {{ max-width: 1400px; margin: auto; padding: 48px; }}
.hero {{
  padding: 34px;
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 28px;
  background: rgba(255,255,255,.055);
  backdrop-filter: blur(22px);
  box-shadow: 0 24px 80px rgba(0,0,0,.35);
}}
.eyebrow {{ color: #8b95a7; font-size: 13px; text-transform: uppercase; letter-spacing: .16em; }}
h1 {{ font-size: 38px; margin: 10px 0 6px; }}
.sub {{ color: #9ca6b6; }}
.grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin:24px 0; }}
.card {{
  padding:20px; border-radius:20px; background:rgba(255,255,255,.055);
  border:1px solid rgba(255,255,255,.08);
}}
.label {{ color:#8e98aa; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
.value {{ font-size:28px; font-weight:700; margin-top:8px; }}
.rate {{ font-size:56px; font-weight:800; margin-top:20px; }}
table {{ width:100%; border-collapse:separate; border-spacing:0; margin-top:24px; overflow:hidden;
  border:1px solid rgba(255,255,255,.08); border-radius:20px; background:rgba(255,255,255,.035); }}
th,td {{ padding:16px 14px; text-align:left; border-bottom:1px solid rgba(255,255,255,.06); }}
th {{ color:#8e98aa; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}
td {{ color:#e9edf4; }}
a {{ color:#b9c7ff; text-decoration:none; }}
.badge {{ padding:6px 10px; border-radius:999px; font-size:11px; font-weight:800; }}
.pass {{ background:rgba(52,211,153,.14); color:#6ee7b7; }}
.fail {{ background:rgba(248,113,113,.14); color:#fca5a5; }}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero">
    <div class="eyebrow">LOAM Data Validator</div>
    <h1>Batch Validation Report</h1>
    <div class="sub">{len(batch_results)} subject / section combinations tested</div>

    <div class="grid">
      <div class="card"><div class="label">Checks</div><div class="value">{total}</div></div>
      <div class="card"><div class="label">Passed</div><div class="value">{passed}</div></div>
      <div class="card"><div class="label">Failed</div><div class="value">{failed}</div></div>
      <div class="card"><div class="label">Missing</div><div class="value">{missing}</div></div>
      <div class="card"><div class="label">Errors</div><div class="value">{errors}</div></div>
    </div>

    <div class="label">Overall Pass Rate</div>
    <div class="rate">{rate}%</div>
  </section>

  <table>
    <thead>
      <tr>
        <th>Grade-Section</th><th>Subject</th><th>Total</th><th>Pass</th>
        <th>Fail</th><th>Missing</th><th>Errors</th><th>Rate</th>
        <th>Status</th><th>Report</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
</body>
</html>"""

    path.write_text(html_content, encoding="utf-8")
    return path


def run_single(args, settings: Settings) -> None:
    if not args.master:
        raise RuntimeError("--master is required unless --batch is used.")
    if not args.subject:
        raise RuntimeError("--subject is required unless --batch is used.")
    if not args.grade_section:
        raise RuntimeError("--grade-section is required unless --batch is used.")

    master = MasterWorkbook(args.master)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        collector = ApiCollector()
        page.on("response", collector.handle_response)

        nav = LoamNavigator(
            page=page,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password,
        )

        print("\n[LOGIN]")
        nav.login()

        validate_one(
            master=master,
            subject=args.subject,
            grade_section=args.grade_section,
            settings=settings,
            nav=nav,
            page=page,
            collector=collector,
            open_report=True,
            report_path="reports/loam_validation_report.html",
            json_path="validation_result.json",
        )

        page.wait_for_timeout(5000)
        browser.close()


def run_batch(args, settings: Settings) -> None:
    master_dir = Path(args.master_dir)

    if not master_dir.exists():
        raise RuntimeError(
            f"Master data folder not found: {master_dir}"
        )

    workbooks = sorted(master_dir.glob("*.xlsx"))
    if not workbooks:
        raise RuntimeError(
            f"No .xlsx files found in {master_dir}"
        )

    # Optional filters are useful while debugging.
    subject_filter = args.subject
    grade_section_filter = args.grade_section

    print("=" * 70)
    print("LOAM BATCH DATA VALIDATION")
    print("=" * 70)
    print(f"Master folder : {master_dir}")
    print(f"Workbooks     : {len(workbooks)}")
    print(f"Subject filter: {subject_filter or 'ALL'}")
    print(f"Section filter: {grade_section_filter or 'ALL'}")
    print("=" * 70)

    batch_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        collector = ApiCollector()
        page.on("response", collector.handle_response)

        nav = LoamNavigator(
            page=page,
            base_url=settings.base_url,
            username=settings.username,
            password=settings.password,
        )

        print("\n[LOGIN]")
        nav.login()

        # Discover subjects once from LOAM.
        subjects = nav.get_subjects()
        if subject_filter:
            subjects = [
                s for s in subjects
                if s.casefold() == subject_filter.casefold()
            ]

        if not subjects:
            raise RuntimeError("No matching subjects found in LOAM.")

        for workbook_path in workbooks:
            grade = _extract_grade_from_filename(workbook_path)

            if grade is None:
                print(
                    f"\n⚠ Skipping {workbook_path.name}: "
                    "could not determine class from filename."
                )
                continue

            if grade_section_filter:
                requested_grade = grade_section_filter.split("-", 1)[0].strip()

                if grade != requested_grade:
                    continue

            print("\n" + "#" * 70)
            print(f"WORKBOOK: {workbook_path.name} | CLASS {grade}")
            print("#" * 70)

            master = MasterWorkbook(str(workbook_path))

            for subject in subjects:
                try:
                    nav.select_subject(subject)
                    available_sections = nav.get_grade_sections()
                except Exception as exc:
                    print(
                        f"⚠ Could not load sections for {subject}: {exc}"
                    )
                    continue

                sections = [
                    gs for gs in available_sections
                    if gs.split("-", 1)[0].strip() == grade
                ]

                if grade_section_filter:
                    sections = [
                        gs for gs in sections
                        if gs.casefold() == grade_section_filter.casefold()
                    ]

                for grade_section in sections:
                    safe_name = re.sub(
                        r"[^A-Za-z0-9_.-]+",
                        "_",
                        f"{grade_section}_{subject}",
                    )

                    report_path = (
                        Path("reports")
                        / "batch"
                        / f"{safe_name}.html"
                    )
                    json_path = (
                        Path("reports")
                        / "batch"
                        / f"{safe_name}.json"
                    )

                    try:
                        all_results, summary = validate_one(
                            master=master,
                            subject=subject,
                            grade_section=grade_section,
                            settings=settings,
                            nav=nav,
                            page=page,
                            collector=collector,
                            open_report=False,
                            report_path=str(report_path),
                            json_path=str(json_path),
                        )

                        batch_results.append(
                            {
                                "grade_section": grade_section,
                                "subject": subject,
                                "master_excel": str(workbook_path),
                                "summary": summary,
                                "report": str(report_path),
                                "json": str(json_path),
                                "results": all_results,
                            }
                        )

                    except Exception as exc:
                        print(
                            f"\n⚠ ERROR — {subject} / {grade_section}: {exc}"
                        )

                        batch_results.append(
                            {
                                "grade_section": grade_section,
                                "subject": subject,
                                "master_excel": str(workbook_path),
                                "summary": {
                                    "total": 0,
                                    "passed": 0,
                                    "failed": 0,
                                    "missing": 0,
                                    "errors": 1,
                                    "pass_rate": 0,
                                },
                                "report": "",
                                "json": "",
                                "results": {},
                            }
                        )

        batch_report = _build_batch_report(
            batch_results,
            "reports/batch_summary.html",
        )

        print("\n" + "=" * 70)
        print("BATCH COMPLETE")
        print("=" * 70)
        print(f"Combinations tested : {len(batch_results)}")
        print(f"Batch report        : {batch_report}")
        print("=" * 70)

        # Open only the single overall batch report.
        import webbrowser
        webbrowser.open(
            batch_report.resolve().as_uri(),
            new=1,
        )

        page.wait_for_timeout(5000)
        browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="LOAM data validator"
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Validate all Excel workbooks in master_data",
    )

    parser.add_argument(
        "--master",
        help="Path to one Master Excel file (single-run mode)",
    )

    parser.add_argument(
        "--master-dir",
        default="master_data",
        help="Folder containing Master Excel files (batch mode)",
    )

    parser.add_argument(
        "--subject",
        help="Subject to test. Optional in batch mode.",
    )

    parser.add_argument(
        "--grade-section",
        help="Grade-Section to test. Optional in batch mode.",
    )

    args = parser.parse_args()
    settings = Settings()

    if not settings.username:
        raise RuntimeError("LOAM_USERNAME is missing from .env")

    if not settings.password:
        raise RuntimeError("LOAM_PASSWORD is missing from .env")

    if args.batch:
        run_batch(args, settings)
    else:
        run_single(args, settings)


if __name__ == "__main__":
    main()
