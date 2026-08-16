from playwright.sync_api import sync_playwright


class Browser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        if self.browser is not None:
            return

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.page = self.browser.new_page()

    def open(self, url: str) -> str:
        self.start()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return f"Opened {url}."

    def search_google(self, query: str) -> str:
        self.start()

        self.page.goto(
            "https://www.google.com",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        search_box = self.page.locator(
            'textarea[name="q"]'
        )

        search_box.fill(query)
        search_box.press("Enter")

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        return f"Searched Google for {query}."

    def close_current_tab(self) -> str:
        if self.page is None:
            return "No browser tab is open."

        self.page.close()

        pages = self.browser.pages

        if pages:
            self.page = pages[-1]
            return "Browser tab closed."

        self.close()

        return "Browser closed."

    def close_all_tabs(self) -> str:
        if self.browser is None:
            return "No browser is open."

        for page in self.browser.pages[:]:
            try:
                page.close()
            except Exception:
                pass

        self.close()

        return "All browser tabs closed."

    def close(self) -> str:
        if self.browser is None:
            return "Browser is already closed."

        try:
            self.browser.close()
        finally:
            if self.playwright is not None:
                self.playwright.stop()

            self.browser = None
            self.playwright = None
            self.page = None

        return "Browser closed."


browser = Browser()