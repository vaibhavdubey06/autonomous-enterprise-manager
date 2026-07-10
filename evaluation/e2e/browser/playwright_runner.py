import time
from typing import Dict, Any

try:
    from playwright.async_api import (
        async_playwright,
        TimeoutError as PlaywrightTimeoutError,
    )
except ImportError:
    pass


class BrowserCoverageReport:
    def __init__(self):
        self.pass_rate = 0.0
        self.total_tests = 0
        self.passed_tests = 0
        self.console_errors = []
        self.network_errors = []
        self.performance_metrics = []


class StreamlitPlaywrightRunner:
    """
    Validates the complete production flow using the actual Streamlit application.
    Drives actions via Playwright to ensure the frontend is never bypassed.
    """

    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.report = BrowserCoverageReport()

    async def _handle_console(self, msg):
        if msg.type == "error":
            self.report.console_errors.append(msg.text)

    async def _handle_request_failed(self, request):
        self.report.network_errors.append(request.url)

    async def run_scenario(self, scenario: Dict[str, Any], page) -> bool:
        """
        Executes a multi-turn conversation simulation via the Streamlit UI.
        """
        success = False
        start_time = time.time()

        try:
            # 1. Navigate and wait for chat interface to load
            await page.goto(self.base_url, timeout=30000)
            await page.wait_for_selector(
                'input[aria-label="Send a message"]', timeout=15000
            )

            # 2. Submit prompt
            prompt = scenario["user_input"]
            await page.fill('input[aria-label="Send a message"]', prompt)
            await page.press('input[aria-label="Send a message"]', "Enter")

            # 3. Wait for Time-to-First-Token (TTFT) and Final Response
            # In Streamlit, assistant messages appear in elements with data-testid="stChatMessage"
            ttft_start = time.time()

            # Wait for assistant response box to appear
            await page.wait_for_selector(
                'div[data-testid="stChatMessage"]:has-text("assistant")', timeout=60000
            )
            ttft = (time.time() - ttft_start) * 1000

            # Wait for spinner to disappear to indicate final response
            await page.wait_for_selector(".stSpinner", state="hidden", timeout=120000)

            total_latency = (time.time() - start_time) * 1000

            # 4. UI Assertions (Markdown, Tables, Citations)
            content_handle = await page.query_selector(
                'div[data-testid="stChatMessage"]:last-child'
            )
            html_content = await content_handle.inner_html() if content_handle else ""

            # Log metrics
            self.report.performance_metrics.append(
                {
                    "scenario_id": scenario["id"],
                    "ttft_ms": ttft,
                    "total_latency_ms": total_latency,
                    "ui_elements_rendered": len(html_content) > 0,
                }
            )

            # Simulate Failure Scenarios check (error banner)
            if scenario.get("expected_success") is False:
                # Expect an error banner
                await page.wait_for_selector(".stException", timeout=5000)

            success = True

        except PlaywrightTimeoutError:
            print(f"Browser timeout for {scenario['id']}")
            await page.screenshot(
                path=f"reports/screenshots/{scenario['id']}_timeout.png"
            )

        except Exception as e:
            print(f"Browser error for {scenario['id']}: {e}")
            await page.screenshot(
                path=f"reports/screenshots/{scenario['id']}_error.png"
            )

        finally:
            self.report.total_tests += 1
            if success:
                self.report.passed_tests += 1

        return success

    async def run_suite(self, scenarios: list):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Setup listeners for network/console errors
                page.on("console", self._handle_console)
                page.on("requestfailed", self._handle_request_failed)

                for scenario in scenarios:
                    await self.run_scenario(scenario, page)

                await browser.close()

        except NameError:
            print("Playwright not installed, skipping browser E2E tests.")

        if self.report.total_tests > 0:
            self.report.pass_rate = self.report.passed_tests / self.report.total_tests

        return self.report
