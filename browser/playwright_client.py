from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:3000"


def run_payment():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        print("Opening Mock Bank...")
        page.goto(f"{BASE_URL}/login.html")

        print("Logging in...")
        page.get_by_label("Username:").fill("demo")
        page.get_by_label("Password:").fill("demo")
        page.get_by_role("button", name="Login").click()

        print("Opening Payments...")
        page.get_by_role("link", name="Payments").click()

        print("Entering payment details...")
        page.get_by_label("From Account:").fill("12345")
        page.get_by_label("To Account:").fill("67890")
        page.get_by_label("Amount:").fill("500")

        print("Submitting payment...")
        page.get_by_role("button", name="Submit Payment").click()

        print("Checking result...")

        result = page.locator("#result")

        result.wait_for()

        text = result.inner_text()

        print()
        print("========== PAYMENT RESULT ==========")
        print(text)
        print("=====================================")

        if "PAYMENT SUCCESSFUL" in text:
            print()
            print("SUCCESS: Playwright completed the payment flow.")
        else:
            print()
            print("FAILURE: Payment success was not detected.")

        input("\nPress Enter to close the browser...")

        browser.close()


if __name__ == "__main__":
    run_payment()
    