


from __future__ import annotations

import html
import webbrowser

from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# HELPERS
# ============================================================

def _esc(value: Any) -> str:
    return html.escape(
        "" if value is None else str(value)
    )


def _status_class(status: str) -> str:
    status = str(status).upper()

    if status == "PASS":
        return "pass"

    if status == "FAIL":
        return "fail"

    if status == "MISSING":
        return "missing"

    return "error"


def _status_icon(status: str) -> str:
    status = str(status).upper()

    if status == "PASS":
        return "✓"

    if status == "FAIL":
        return "×"

    if status == "MISSING":
        return "!"

    return "⚠"


def _format_value(value: Any) -> str:

    if value is None:
        return "—"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


# ============================================================
# BUILD HTML REPORT
# ============================================================

def build_html_report(
    *,
    subject: str,
    exam: str,
    grade_section: str,
    master_excel: str,
    tolerance: float,
    all_results: dict,
    report_links: dict[str, str] | None = None,
) -> str:

    # --------------------------------------------------------
    # New combined structure:
    #
    # {
    #     "11-A": {
    #         "summary": {...},
    #         "results": {
    #             "Individual Student Marks": [...],
    #             ...
    #         }
    #     },
    #     "11-B": {
    #         ...
    #     }
    # }
    # --------------------------------------------------------

    # ========================================================
    # OVERALL STATISTICS
    # ========================================================

    total = 0
    passed = 0
    failed = 0
    missing = 0
    errors = 0

    for section_data in all_results.values():

        summary = section_data.get("summary", {})

        total += summary.get("total", 0)
        passed += summary.get("passed", 0)
        failed += summary.get("failed", 0)
        missing += summary.get("missing", 0)
        errors += summary.get("errors", 0)

    pass_rate = (
        round(passed / total * 100, 2)
        if total
        else 0
    )

    overall_status = (
        "PASS"
        if failed == 0
        and missing == 0
        and errors == 0
        else "FAIL"
    )

    generated_at = datetime.now().strftime(
        "%d %b %Y · %I:%M:%S %p"
    )
    if grade_section and grade_section != "ALL":
        subtitle_section = _esc(grade_section)
    else:
        subtitle_section = f"{len(all_results)} Grade-Section(s)"

    # ========================================================
    # CHECK CARDS
    # ========================================================
    #
    # Combine the same check across all Grade-Sections.
    #
    # Example:
    #
    # Individual Student Marks
    # 11-A → 40 records
    # 11-B → 40 records
    # 12-A → 35 records
    #
    # The report shows one combined card.
    # ========================================================

    combined_checks = {}

    for section_data in all_results.values():

        section_results = section_data.get(
            "results",
            {},
        )

        for check_name, results in section_results.items():

            if check_name not in combined_checks:
                combined_checks[check_name] = []

            combined_checks[check_name].extend(results)

    check_cards = []

    for check_name, results in combined_checks.items():

        check_total = len(results)

        check_passed = sum(
            r.get("status") == "PASS"
            for r in results
        )

        check_failed = sum(
            r.get("status") == "FAIL"
            for r in results
        )

        check_missing = sum(
            r.get("status") == "MISSING"
            for r in results
        )

        check_errors = sum(
            r.get("status") == "ERROR"
            for r in results
        )

        check_ok = (
            check_failed == 0
            and check_missing == 0
            and check_errors == 0
        )

        icon = "✓" if check_ok else "×"

        card_class = (
            "check-pass"
            if check_ok
            else "check-fail"
        )

        check_percentage = (
            round(
                check_passed / check_total * 100,
                1,
            )
            if check_total
            else 0
        )

        check_cards.append(
            f"""
            <div class="check-card {card_class}">

                <div class="check-icon">
                    {icon}
                </div>

                <div class="check-info">

                    <div class="check-title">
                        {_esc(check_name)}
                    </div>

                    <div class="check-meta">
                        {check_passed} of {check_total}
                        records passed
                    </div>

                    <div class="progress-track">
                        <div
                            class="progress-fill"
                            style="width:{check_percentage}%"
                        ></div>
                    </div>

                </div>

                <div class="check-percent">
                    {check_percentage}%
                </div>

            </div>
            """
        )

    # ========================================================
    # GRADE-SECTION SUMMARY
    # ========================================================

    grade_section_rows = []

    for section_name, section_data in all_results.items():

        summary = section_data.get(
            "summary",
            {},
        )

        section_status = (
            "PASS"
            if summary.get("failed", 0) == 0
            and summary.get("missing", 0) == 0
            and summary.get("errors", 0) == 0
            else "FAIL"
        )

        status_class = (
            "pass"
            if section_status == "PASS"
            else "fail"
        )

        report_link_html = "<span class='muted'>—</span>"

        if report_links and section_name in report_links:
            report_href = _esc(report_links[section_name])

            report_link_html = f"""
                <a
                    class="view-report-btn"
                    href="{report_href}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    View Report
                </a>
            """

        grade_section_rows.append(
            f"""
            <tr>

                <td>
                    <div class="record-name">
                        {_esc(section_name)}
                    </div>
                </td>

                <td class="number">
                    {summary.get("total", 0)}
                </td>

                <td class="number">
                    {summary.get("passed", 0)}
                </td>

                <td class="number">
                    {summary.get("failed", 0)}
                </td>

                <td class="number">
                    {summary.get("missing", 0)}
                </td>

                <td class="number">
                    {summary.get("errors", 0)}
                </td>

                <td class="number">
                    {summary.get("pass_rate", 0)}%
                </td>

                <td>
                    <span class="status {status_class}">
                        {_status_icon(section_status)}
                        {_esc(section_status)}
                    </span>
                </td>

                <td>
                    {report_link_html}
                </td>

            </tr>
            """
        )

    # ========================================================
    # FAILURE SECTIONS
    # ========================================================

    failure_sections = []

    for section_name, section_data in all_results.items():

        section_results = section_data.get(
            "results",
            {},
        )

        for check_name, results in section_results.items():

            failures = [
                r
                for r in results
                if r.get("status")
                in {
                    "FAIL",
                    "MISSING",
                    "ERROR",
                }
            ]

            if not failures:
                continue

            rows = []

            for result in failures:

                status = result.get(
                    "status",
                    "ERROR",
                )

                roll = result.get(
                    "roll_number"
                )

                student = result.get(
                    "student_name"
                )

                question = result.get(
                    "question"
                )

                chapter = result.get(
                    "chapter"
                )

                api_value = result.get(
                    "api_value"
                )

                excel_value = result.get(
                    "excel_value"
                )

                difference = result.get(
                    "difference"
                )

                identifier_parts = [
                    f"Section {_esc(section_name)}"
                ]

                if roll is not None:
                    identifier_parts.append(
                        f"Roll {roll}"
                    )

                if student:
                    identifier_parts.append(
                        _esc(student)
                    )

                if question is not None:
                    identifier_parts.append(
                        f"Q{_esc(question)}"
                    )

                if chapter:
                    identifier_parts.append(
                        _esc(chapter)
                    )

                identifier = " · ".join(
                    identifier_parts
                )

                if difference is None:
                    difference_text = "—"
                else:
                    difference_text = (
                        f"{difference:.2f}"
                    )

                status_class = _status_class(
                    status
                )

                rows.append(
                    f"""
                    <tr>

                        <td>
                            <div class="record-name">
                                {_esc(identifier)}
                            </div>
                        </td>

                        <td class="number api-cell">
                            {_format_value(api_value)}
                        </td>

                        <td class="number master-cell">
                            {_format_value(excel_value)}
                        </td>

                        <td class="number difference-cell">
                            {difference_text}
                        </td>

                        <td>
                            <span class="status {status_class}">
                                <span>
                                    {_status_icon(status)}
                                </span>
                                {_esc(status)}
                            </span>
                        </td>

                        <td class="reason">
                            {_esc(
                                result.get(
                                    "message",
                                    "",
                                )
                            )}
                        </td>

                    </tr>
                    """
                )

            failure_sections.append(
                f"""
                <section class="failure-section">

                    <div class="failure-heading">

                        <div class="failure-heading-left">

                            <div class="failure-alert">
                                !
                            </div>

                            <div>

                                <div class="failure-title">
                                    {_esc(check_name)}
                                </div>

                                <div class="failure-subtitle">
                                    Grade-Section:
                                    {_esc(section_name)}
                                    ·
                                    {len(failures)}
                                    mismatch(es) detected
                                </div>

                            </div>

                        </div>

                        <div class="failure-count">
                            {len(failures)}
                        </div>

                    </div>

                    <div class="table-wrap">

                        <table>

                            <thead>
                                <tr>
                                    <th>Record</th>
                                    <th>LOAM</th>
                                    <th>Master</th>
                                    <th>Difference</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                    <th>Details</th>
                                </tr>
                            </thead>

                            <tbody>
                                {''.join(rows)}
                            </tbody>

                        </table>

                    </div>

                </section>
                """
            )

    # ========================================================
    # NO FAILURE STATE
    # ========================================================

    if not failure_sections:

        failure_content = """
        <div class="all-good">

            <div class="all-good-icon">
                ✓
            </div>

            <div>

                <div class="all-good-title">
                    Everything looks good
                </div>

                <div class="all-good-subtitle">
                    All validation checks are within
                    the configured tolerance.
                </div>

            </div>

        </div>
        """

    else:

        failure_content = "".join(
            failure_sections
        )

    # ========================================================
    # GRADE-SECTION TABLE
    # ========================================================

    grade_section_table = f"""
    <div class="section-title-row">

        <div class="section-title">
            Grade-Section Summary
        </div>

        <div class="section-hint">
            {len(all_results)} Grade-Section(s) tested
        </div>

    </div>

    <section class="failure-section"
             style="margin-bottom:34px;">

        <div class="table-wrap">

            <table>

                <thead>
                    <tr>
                        <th>Grade-Section</th>
                        <th>Total</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Missing</th>
                        <th>Errors</th>
                        <th>Pass Rate</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    {''.join(grade_section_rows)}
                </tbody>

            </table>

        </div>

    </section>
    """

    # ========================================================
    # HTML
    # ========================================================

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    LOAM · Validation Report
</title>


<style>

/* ==========================================================
   ROOT
   ========================================================== */

:root {{

    --bg: #07090d;
    --bg-2: #0b0e14;

    --glass: rgba(255,255,255,.045);
    --glass-strong: rgba(255,255,255,.065);

    --border: rgba(255,255,255,.09);
    --border-bright: rgba(255,255,255,.14);

    --text: #f4f7fb;
    --text-soft: #c6ccd7;
    --muted: #7f8999;

    --green: #4ade80;
    --green-soft: rgba(74,222,128,.11);

    --red: #fb7185;
    --red-soft: rgba(251,113,133,.11);

    --amber: #fbbf24;
    --amber-soft: rgba(251,191,36,.11);

    --blue: #60a5fa;

    --radius: 22px;

    --shadow:
        0 20px 70px rgba(0,0,0,.38);

}}


/* ==========================================================
   RESET
   ========================================================== */

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{

    margin: 0;

    min-height: 100vh;

    color: var(--text);

    background:

        radial-gradient(
            circle at 10% 0%,
            rgba(96,165,250,.10),
            transparent 28%
        ),

        radial-gradient(
            circle at 90% 10%,
            rgba(74,222,128,.075),
            transparent 26%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(139,92,246,.07),
            transparent 30%
        ),

        var(--bg);

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    letter-spacing: -.01em;
}}


/* ==========================================================
   BACKGROUND GRID
   ========================================================== */

body::before {{

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    opacity: .20;

    background-image:

        linear-gradient(
            rgba(255,255,255,.025) 1px,
            transparent 1px
        ),

        linear-gradient(
            90deg,
            rgba(255,255,255,.025) 1px,
            transparent 1px
        );

    background-size: 42px 42px;

    mask-image:
        linear-gradient(
            to bottom,
            black,
            transparent 80%
        );

}}


/* ==========================================================
   LAYOUT
   ========================================================== */

.container {{

    width: min(
        1240px,
        calc(100% - 40px)
    );

    margin: 0 auto;

    padding: 48px 0 80px;

    position: relative;

    z-index: 1;

}}


/* ==========================================================
   GLASS
   ========================================================== */

.glass {{

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );

    border:
        1px solid var(--border);

    box-shadow:
        var(--shadow),
        inset 0 1px 0 rgba(255,255,255,.045);

    backdrop-filter:
        blur(24px);

    -webkit-backdrop-filter:
        blur(24px);

}}


/* ==========================================================
   HEADER
   ========================================================== */

.header {{

    display: flex;

    justify-content: space-between;

    align-items: flex-start;

    gap: 24px;

    margin-bottom: 22px;

    animation:
        fadeUp .55s ease both;

}}

.brand {{

    display: flex;

    align-items: center;

    gap: 16px;

}}

.logo {{

    width: 50px;

    height: 50px;

    display: grid;

    place-items: center;

    border-radius: 16px;

    font-size: 19px;

    font-weight: 900;

    color: white;

    background:

        linear-gradient(
            135deg,
            #1f2937,
            #111827
        );

    border:
        1px solid rgba(255,255,255,.12);

    box-shadow:
        0 12px 35px rgba(0,0,0,.3),
        inset 0 1px 0 rgba(255,255,255,.08);

}}

.logo::after {{

    content: "";

    position: absolute;

    width: 8px;

    height: 8px;

    margin:
        30px 0 0 30px;

    border-radius: 50%;

    background: var(--green);

    box-shadow:
        0 0 14px var(--green);

}}

h1 {{

    margin: 0;

    font-size: clamp(
        26px,
        4vw,
        34px
    );

    font-weight: 850;

    letter-spacing: -.055em;

}}

.subtitle {{

    margin-top: 7px;

    color: var(--muted);

    font-size: 14px;

}}

.verdict {{

    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding: 9px 14px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: 850;

    letter-spacing: .05em;

    border: 1px solid;

}}

.verdict::before {{

    content: "";

    width: 7px;

    height: 7px;

    border-radius: 50%;

}}

.verdict.pass {{

    color: var(--green);

    background: var(--green-soft);

    border-color:
        rgba(74,222,128,.20);

}}

.verdict.pass::before {{

    background: var(--green);

    box-shadow:
        0 0 12px var(--green);

}}

.verdict.fail {{

    color: var(--red);

    background: var(--red-soft);

    border-color:
        rgba(251,113,133,.20);

}}

.verdict.fail::before {{

    background: var(--red);

    box-shadow:
        0 0 12px var(--red);

}}


/* ==========================================================
   META
   ========================================================== */

.meta {{

    display: grid;

    grid-template-columns:
        repeat(4, minmax(0,1fr));

    gap: 1px;

    margin-bottom: 16px;

    border-radius: var(--radius);

    overflow: hidden;

    background:
        var(--border);

    border:
        1px solid var(--border);

    box-shadow: var(--shadow);

    backdrop-filter: blur(24px);

}}

.meta-item {{

    min-width: 0;

    padding: 19px 20px;

    background:
        rgba(255,255,255,.035);

}}

.meta-item:hover {{

    background:
        rgba(255,255,255,.055);

}}

.meta-label {{

    color: var(--muted);

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: .12em;

    font-weight: 800;

}}

.meta-value {{

    margin-top: 7px;

    color: var(--text-soft);

    font-size: 14px;

    font-weight: 700;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}}


/* ==========================================================
   METRICS
   ========================================================== */

.metrics {{

    display: grid;

    grid-template-columns:
        repeat(4, minmax(0,1fr));

    gap: 14px;

    margin-bottom: 34px;

}}

.metric {{

    position: relative;

    overflow: hidden;

    padding: 21px;

    border-radius: var(--radius);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.025)
        );

    border:
        1px solid var(--border);

    box-shadow:
        var(--shadow),
        inset 0 1px 0 rgba(255,255,255,.04);

    backdrop-filter:
        blur(22px);

    animation:
        fadeUp .55s ease both;

}}

.metric::after {{

    content: "";

    position: absolute;

    width: 120px;

    height: 120px;

    right: -55px;

    top: -55px;

    border-radius: 50%;

    background:
        rgba(255,255,255,.025);

    filter: blur(2px);

}}

.metric-label {{

    color: var(--muted);

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: .12em;

    font-weight: 800;

}}

.metric-value {{

    margin-top: 8px;

    font-size: 34px;

    line-height: 1;

    font-weight: 900;

    letter-spacing: -.055em;

}}

.metric.rate .metric-value {{
    color: var(--blue);
}}

.metric.pass .metric-value {{
    color: var(--green);
}}

.metric.fail .metric-value {{
    color: var(--red);
}}

.metric.rate {{
    border-color:
        rgba(96,165,250,.18);
}}

.metric.pass {{
    border-color:
        rgba(74,222,128,.16);
}}

.metric.fail {{
    border-color:
        rgba(251,113,133,.18);
}}


/* ==========================================================
   SECTION TITLE
   ========================================================== */

.section-title-row {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;

    margin:
        0 0 14px;

}}

.section-title {{

    font-size: 17px;

    font-weight: 850;

    letter-spacing: -.025em;

}}

.section-hint {{

    color: var(--muted);

    font-size: 12px;

}}


/* ==========================================================
   CHECK GRID
   ========================================================== */

.check-grid {{

    display: grid;

    grid-template-columns:
        repeat(2, minmax(0,1fr));

    gap: 13px;

    margin-bottom: 36px;

}}

.check-card {{

    min-width: 0;

    display: flex;

    align-items: center;

    gap: 14px;

    padding: 17px;

    border-radius: 19px;

    background:
        rgba(255,255,255,.035);

    border:
        1px solid var(--border);

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.035);

    backdrop-filter:
        blur(20px);

    transition:
        transform .2s ease,
        background .2s ease,
        border-color .2s ease;

}}

.check-card:hover {{

    transform:
        translateY(-2px);

    background:
        rgba(255,255,255,.055);

    border-color:
        var(--border-bright);

}}

.check-pass {{
    border-left:
        3px solid var(--green);
}}

.check-fail {{
    border-left:
        3px solid var(--red);
}}

.check-icon {{

    flex:
        0 0 auto;

    width: 38px;

    height: 38px;

    display: grid;

    place-items: center;

    border-radius: 12px;

    font-size: 16px;

    font-weight: 900;

}}

.check-pass .check-icon {{

    color: var(--green);

    background:
        var(--green-soft);

    box-shadow:
        0 0 24px rgba(74,222,128,.06);

}}

.check-fail .check-icon {{

    color: var(--red);

    background:
        var(--red-soft);

}}

.check-info {{
    flex: 1;
    min-width: 0;
}}

.check-title {{

    font-size: 13px;

    font-weight: 800;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}}

.check-meta {{

    margin-top: 4px;

    color: var(--muted);

    font-size: 11px;

}}

.check-percent {{

    flex:
        0 0 auto;

    font-size: 12px;

    font-weight: 850;

    color: var(--text-soft);

}}

.progress-track {{

    height: 4px;

    margin-top: 9px;

    border-radius: 99px;

    overflow: hidden;

    background:
        rgba(255,255,255,.07);

}}

.progress-fill {{

    height: 100%;

    border-radius: inherit;

    background:
        var(--green);

    box-shadow:
        0 0 10px rgba(74,222,128,.25);

}}


/* ==========================================================
   FAILURE SECTION
   ========================================================== */

.failure-section {{

    margin-bottom: 16px;

    overflow: hidden;

    border-radius: var(--radius);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(255,255,255,.025)
        );

    border:
        1px solid rgba(251,113,133,.13);

    box-shadow:
        var(--shadow);

    backdrop-filter:
        blur(24px);

}}

.failure-heading {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 16px;

    padding: 18px 20px;

    border-bottom:
        1px solid var(--border);

}}

.failure-heading-left {{

    display: flex;

    align-items: center;

    gap: 13px;

}}

.failure-alert {{

    width: 36px;

    height: 36px;

    display: grid;

    place-items: center;

    border-radius: 11px;

    color: var(--red);

    background:
        var(--red-soft);

    font-weight: 900;

}}

.failure-title {{

    font-size: 14px;

    font-weight: 850;

}}

.failure-subtitle {{

    margin-top: 4px;

    color: var(--muted);

    font-size: 11px;

}}

.failure-count {{

    min-width: 34px;

    height: 28px;

    padding: 0 9px;

    display: grid;

    place-items: center;

    border-radius: 999px;

    color: var(--red);

    background:
        var(--red-soft);

    font-size: 11px;

    font-weight: 900;

}}


/* ==========================================================
   TABLE
   ========================================================== */

.table-wrap {{

    overflow-x: auto;

}}

table {{

    width: 100%;

    border-collapse: collapse;

}}

thead {{

    background:
        rgba(0,0,0,.17);

}}

th {{

    text-align: left;

    padding: 12px 15px;

    color: var(--muted);

    font-size: 9px;

    text-transform: uppercase;

    letter-spacing: .1em;

    font-weight: 850;

    white-space: nowrap;

}}

td {{

    padding: 14px 15px;

    border-top:
        1px solid rgba(255,255,255,.055);

    color: var(--text-soft);

    font-size: 12px;

}}

tbody tr {{

    transition:
        background .15s ease;

}}

tbody tr:hover {{

    background:
        rgba(255,255,255,.025);

}}

.record-name {{

    color: var(--text);

    font-weight: 700;

}}

.number {{

    font-variant-numeric:
        tabular-nums;

    font-weight: 750;

}}

.api-cell {{
    color: #93c5fd;
}}

.master-cell {{
    color: #c4b5fd;
}}

.difference-cell {{
    color: var(--red);
}}

.reason {{

    min-width: 230px;

    color: var(--muted);

    line-height: 1.45;

}}


/* ==========================================================
   STATUS
   ========================================================== */

.status {{

    display: inline-flex;

    align-items: center;

    gap: 5px;

    padding: 5px 9px;

    border-radius: 999px;

    font-size: 9px;

    font-weight: 900;

    letter-spacing: .07em;

    border: 1px solid;

}}

.status.pass {{

    color: var(--green);

    background:
        var(--green-soft);

    border-color:
        rgba(74,222,128,.16);

}}

.status.fail {{

    color: var(--red);

    background:
        var(--red-soft);

    border-color:
        rgba(251,113,133,.16);

}}

.status.missing {{

    color: var(--amber);

    background:
        var(--amber-soft);

    border-color:
        rgba(251,191,36,.16);

}}

.status.error {{

    color: var(--red);

    background:
        var(--red-soft);

    border-color:
        rgba(251,113,133,.16);

}}


/* ==========================================================
   ALL GOOD
   ========================================================== */

.all-good {{

    display: flex;

    align-items: center;

    gap: 15px;

    padding: 23px;

    border-radius: var(--radius);

    background:
        linear-gradient(
            145deg,
            rgba(74,222,128,.08),
            rgba(74,222,128,.025)
        );

    border:
        1px solid rgba(74,222,128,.16);

    box-shadow:
        var(--shadow);

}}

.all-good-icon {{

    width: 43px;

    height: 43px;

    flex: 0 0 auto;

    display: grid;

    place-items: center;

    border-radius: 13px;

    color: var(--green);

    background:
        var(--green-soft);

    font-weight: 900;

    font-size: 18px;

}}

.all-good-title {{

    font-weight: 850;

    font-size: 14px;

}}

.all-good-subtitle {{

    margin-top: 4px;

    color: var(--muted);

    font-size: 12px;

}}


/* ==========================================================
   FOOTER
   ========================================================== */

.footer {{

    margin-top: 34px;

    text-align: center;

    color: var(--muted);

    font-size: 11px;

}}


/* ==========================================================
   ANIMATION
   ========================================================== */

@keyframes fadeUp {{

    from {{
        opacity: 0;
        transform: translateY(8px);
    }}

    to {{
        opacity: 1;
        transform: translateY(0);
    }}

}}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (max-width: 900px) {{

    .meta,
    .metrics {{
        grid-template-columns:
            repeat(2, minmax(0,1fr));
    }}

}}

@media (max-width: 700px) {{

    .container {{
        width:
            min(
                calc(100% - 24px),
                1240px
            );

        padding-top: 28px;
    }}

    .header {{
        flex-direction: column;
    }}

    .meta,
    .metrics,
    .check-grid {{
        grid-template-columns: 1fr;
    }}

    .section-hint {{
        display: none;
    }}

    th,
    td {{
        padding:
            11px 10px;
    }}

}}

.download-report-btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border: 1px solid var(--border-bright);
    border-radius: 10px;
    background: rgba(255,255,255,.06);
    color: var(--text);
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
    transition: .2s ease;
}}

.download-report-btn:hover {{
    background: rgba(255,255,255,.12);
    transform: translateY(-1px);
}}

.report-actions {{
    display: flex;
    justify-content: flex-end;
    margin-bottom: 16px;
}}

.view-report-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 7px 11px;
    border-radius: 9px;
    border: 1px solid rgba(96,165,250,.20);
    background: rgba(96,165,250,.08);
    color: var(--blue);
    font-size: 10px;
    font-weight: 850;
    text-decoration: none;
    white-space: nowrap;
    transition: .2s ease;
}}

.view-report-btn:hover {{
    background: rgba(96,165,250,.16);
    border-color: rgba(96,165,250,.35);
    transform: translateY(-1px);
}}

</style>

</head>


<body>

<div class="container">

    <div class="report-actions">
        <button class="download-report-btn" onclick="downloadReport()">
            ↓ Download Report
        </button>
    </div>


    <!-- =====================================================
         HEADER
         ================================================== -->

    <header class="header">

        <div class="brand">

            <div class="logo">
                L
            </div>

            <div>

                <h1>
                    LOAM Data Validation
                </h1>

                <div class="subtitle">
                    {_esc(subject)}
                    ·
                    {_esc(exam)}
                    ·
                    {subtitle_section}
                </div>

            </div>

        </div>


        <div class="verdict {_esc(
            overall_status.lower()
        )}">

            {_esc(overall_status)}

        </div>

    </header>


    <!-- =====================================================
         META
         ================================================== -->

    <div class="meta">

        <div class="meta-item">

            <div class="meta-label">
                Subject
            </div>

            <div class="meta-value">
                {_esc(subject)}
            </div>

        </div>


        <div class="meta-item">

            <div class="meta-label">
                Exam
            </div>

            <div class="meta-value">
                {_esc(exam)}
            </div>

        </div>


        <div class="meta-item">

            <div class="meta-label">
                Master Excel
            </div>

            <div class="meta-value">
                {_esc(
                    Path(master_excel).name
                )}
            </div>

        </div>


        <div class="meta-item">

            <div class="meta-label">
                Generated
            </div>

            <div class="meta-value">
                {_esc(generated_at)}
            </div>

        </div>

    </div>


    <!-- =====================================================
         METRICS
         ================================================== -->

    <div class="metrics">

        <div class="metric rate">

            <div class="metric-label">
                Pass Rate
            </div>

            <div class="metric-value">
                {pass_rate:.2f}%
            </div>

        </div>


        <div class="metric pass">

            <div class="metric-label">
                Passed
            </div>

            <div class="metric-value">
                {passed}
            </div>

        </div>


        <div class="metric fail">

            <div class="metric-label">
                Failed
            </div>

            <div class="metric-value">
                {failed}
            </div>

        </div>


        <div class="metric">

            <div class="metric-label">
                Total Records
            </div>

            <div class="metric-value">
                {total}
            </div>

        </div>

    </div>

    {grade_section_table}


    <!-- =====================================================
         CHECKS
         ================================================== -->

    
    <div class="section-title-row">

        <div class="section-title">
            Validation Checks
        </div>

        <div class="section-hint">
            Tolerance ±{tolerance}
        </div>

    </div>


    <div class="check-grid">

        {''.join(check_cards)}

    </div>


    <!-- =====================================================
         FAILURES
         ================================================== -->

    <div class="section-title-row">

        <div class="section-title">
            Mismatches & Failure Details
        </div>

        <div class="section-hint">
            LOAM vs Master
        </div>

    </div>


    {failure_content}


    <!-- =====================================================
         FOOTER
         ================================================== -->

    <div class="footer">

        LOAM Data Validation
        ·
        Tolerance ±{tolerance}
        ·
        Generated { _esc(generated_at) }

    </div>


</div>

<script>
function downloadReport() {{
    const html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;

    const blob = new Blob([html], {{
        type: 'text/html;charset=utf-8'
    }});

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = 'LOAM_Validation_Report.html';

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}}
</script>

</body>

</html>
"""


# ============================================================
# WRITE + OPEN REPORT
# ============================================================

def write_and_open_report(
    *,
    subject: str,
    exam: str,
    grade_section: str,
    master_excel: str,
    tolerance: float,
    all_results: dict[str, list[dict]],
    output_path: str = (
        "reports/loam_validation_report.html"
    ),
) -> Path:

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    html_content = build_html_report(
        subject=subject,
        exam=exam,
        grade_section=grade_section,
        master_excel=master_excel,
        tolerance=tolerance,
        all_results=all_results,
    )

    path.write_text(
        html_content,
        encoding="utf-8",
    )

    # Open report in a new browser tab/window.
    webbrowser.open(
        path.resolve().as_uri(),
        new=1,
    )

    return path