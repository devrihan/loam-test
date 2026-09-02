


from __future__ import annotations


from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)


class LoamNavigator:
    """
    Handles only LOAM browser navigation.

    Responsibilities:
    - Login
    - Wait for dashboard filters
    - Read available subjects
    - Select a subject
    - Read available Grade-Sections
    - Select a Grade-Section
    - Open Chapter
    - Open Students
    - Open Questions
    """

    def __init__(
        self,
        page: Page,
        base_url: str,
        username: str,
        password: str,
    ):
        self.page = page
        self.base_url = base_url
        self.username = username
        self.password = password

    # =========================================================
    # LOGIN
    # =========================================================

    def login(self) -> None:
        print("Opening LOAM login page...")

        self.page.goto(
            self.base_url,
            wait_until="domcontentloaded",
        )

        print("Entering username...")

        self.page.get_by_role(
            "textbox",
            name="Username",
        ).fill(self.username)

        print("Entering password...")

        self.page.get_by_role(
            "textbox",
            name="Password",
        ).fill(self.password)

        print("Clicking Sign In...")

        self.page.get_by_role(
            "button",
            name="Sign In",
        ).click()

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        print("✓ Logged in")
        print("✓ Dashboard opened")

        self.wait_for_filters()

    # =========================================================
    # DASHBOARD FILTERS
    # =========================================================

    def wait_for_filters(self) -> None:
        """
        Wait until Subject and Grade-Sec filters
        have rendered on the dashboard.
        """

        print(
            "Waiting for dashboard filters to load..."
        )

        try:
            self.page.locator(
                "button"
            ).filter(
                has_text="Subject:"
            ).first.wait_for(
                state="visible",
                timeout=15000,
            )

            self.page.locator(
                "button"
            ).filter(
                has_text="Grade-Sec:"
            ).first.wait_for(
                state="visible",
                timeout=15000,
            )

        except PlaywrightTimeoutError:
            raise RuntimeError(
                "Dashboard filters did not load."
            )

        print(
            "✓ Dashboard filters loaded"
        )

    # =========================================================
    # SUBJECT
    # =========================================================

    def get_subjects(self) -> list[str]:
        """
        Open Subject dropdown and return all
        available subjects.
        """

        trigger = self._subject_trigger()

        trigger.click()

        self.page.get_by_role(
            "option"
        ).first.wait_for(
            state="visible",
            timeout=5000,
        )

        options = self.page.get_by_role(
            "option"
        )

        subjects = []

        for i in range(options.count()):

            text = (
                options.nth(i)
                .inner_text()
                .strip()
            )

            if text:
                subjects.append(text)

        self.page.keyboard.press(
            "Escape"
        )

        subjects = list(
            dict.fromkeys(subjects)
        )

        if not subjects:
            raise RuntimeError(
                "No subjects found in Subject dropdown."
            )

        return subjects

    def select_subject(
        self,
        subject: str,
    ) -> None:

        print(
            f"Selecting Subject → {subject}"
        )

        trigger = self._subject_trigger()

        trigger.click()

        option = self.page.get_by_role(
            "option",
            name=subject,
            exact=True,
        )

        option.wait_for(
            state="visible",
            timeout=5000,
        )

        option.click()

        self.page.wait_for_timeout(
            1000
        )

        print(
            f"✓ Subject selected → {subject}"
        )

    # =========================================================
    # GRADE-SECTION
    # =========================================================

    def get_grade_sections(self) -> list[str]:
        """
        Open Grade-Sec dropdown and return all
        available Grade-Section combinations.
        """

        trigger = self._grade_section_trigger()

        trigger.click()

        self.page.get_by_role(
            "option"
        ).first.wait_for(
            state="visible",
            timeout=5000,
        )

        options = self.page.get_by_role(
            "option"
        )

        grade_sections = []

        for i in range(options.count()):

            text = (
                options.nth(i)
                .inner_text()
                .strip()
            )

            if text:
                grade_sections.append(text)

        self.page.keyboard.press(
            "Escape"
        )

        grade_sections = list(
            dict.fromkeys(grade_sections)
        )

        if not grade_sections:
            raise RuntimeError(
                "No Grade-Section options found."
            )

        return grade_sections

    def select_grade_section(
        self,
        grade_section: str,
    ) -> None:

        print(
            f"Selecting Grade-Sec → "
            f"{grade_section}"
        )

        trigger = self._grade_section_trigger()

        trigger.click()

        option = self.page.get_by_role(
            "option",
            name=grade_section,
            exact=True,
        )

        option.wait_for(
            state="visible",
            timeout=5000,
        )

        option.click()

        self.page.wait_for_timeout(
            1500
        )

        print(
            f"✓ Grade-Sec selected → "
            f"{grade_section}"
        )

    # =========================================================
    # CHAPTER
    # =========================================================

    def go_to_chapter(self) -> None:
        """
        Open the Chapter page.

        LOAM sidebar uses:
            Chapter -> /chapter

        We use the accessible link name instead
        of relying on CSS classes.
        """

        print(
            "Opening Chapter tab..."
        )

        link = self.page.get_by_role(
            "link",
            name="Chapter",
            exact=True,
        )

        link.wait_for(
            state="visible",
            timeout=10000,
        )

        link.click()

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        self.page.wait_for_timeout(
            1500
        )

        print(
            "✓ Chapter tab opened"
        )

    # =========================================================
    # STUDENTS
    # =========================================================

    def go_to_students(self) -> None:

        print(
            "Opening Students tab..."
        )

        link = self.page.get_by_role(
            "link",
            name="Students",
            exact=True,
        )

        link.wait_for(
            state="visible",
            timeout=10000,
        )

        link.click()

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        self.page.wait_for_timeout(
            1500
        )

        print(
            "✓ Students tab opened"
        )

    # =========================================================
    # QUESTIONS
    # =========================================================

    def go_to_questions(self) -> None:

        print(
            "Opening Questions tab..."
        )

        link = self.page.get_by_role(
            "link",
            name="Questions",
            exact=True,
        )

        link.wait_for(
            state="visible",
            timeout=10000,
        )

        link.click()

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        self.page.wait_for_timeout(
            1500
        )

        print(
            "✓ Questions tab opened"
        )

    # =========================================================
    # DASHBOARD / HOME
    # =========================================================

    def go_to_dashboard(self) -> None:

        print(
            "Opening Dashboard..."
        )

        link = self.page.get_by_role(
            "link",
            name="Home",
            exact=True,
        )

        link.wait_for(
            state="visible",
            timeout=10000,
        )

        link.click()

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        self.wait_for_filters()

        print(
            "✓ Dashboard opened"
        )

    # =========================================================
    # INTERNAL SELECTOR HELPERS
    # =========================================================

    def _subject_trigger(self):

        trigger = self.page.locator(
            "button"
        ).filter(
            has_text="Subject:"
        ).first

        if trigger.count() == 0:
            raise RuntimeError(
                "Subject dropdown trigger "
                "could not be found."
            )

        return trigger

    def _grade_section_trigger(self):

        trigger = self.page.locator(
            "button"
        ).filter(
            has_text="Grade-Sec:"
        ).first

        if trigger.count() == 0:
            raise RuntimeError(
                "Grade-Sec dropdown trigger "
                "could not be found."
            )

        return trigger