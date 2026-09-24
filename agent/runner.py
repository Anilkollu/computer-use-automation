import argparse

from playwright.sync_api import sync_playwright

from agent.llm import get_next_action


BASE_URL = "http://127.0.0.1:3000"


def get_page_state(page):
    state = page.locator("body").inner_text()

    inputs = page.locator("input")

    for i in range(inputs.count()):
        field = inputs.nth(i)

        try:
            label = field.get_attribute("id") or field.get_attribute("name")
            value = field.input_value()

            if label:
                state += f"\nFIELD {label}: {value}"
        except Exception:
            pass

    return state


def execute_action(page, action):
    action_type = action.get("action")

    if action_type == "click":
        target = action["target"]

        print(f"  ACTION: click -> {target}")

        try:
            page.get_by_role(
                "button",
                name=target
            ).click(timeout=3000)
        except Exception:
            page.get_by_role(
                "link",
                name=target
            ).click(timeout=3000)

        return

    if action_type == "fill":
        target = action["target"]
        value = action["value"]

        print(f"  ACTION: fill -> {target}")

        page.get_by_label(target).fill(value)

        return

    if action_type == "finish":
        print("  ACTION: finish")
        return

    raise RuntimeError(
        f"Unsupported action: {action_type}"
    )


def run_agent(goal):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        print("Opening Mock Bank...")
        page.goto(f"{BASE_URL}/login.html")

        max_steps = 15

        for step in range(1, max_steps + 1):
            print()
            print(f"========== STEP {step} ==========")

            page_text = get_page_state(page)

            print("CURRENT PAGE:")
            print(page_text)

            if "PAYMENT SUCCESSFUL" in page_text:
                print()
                print("SUCCESS: Goal completed.")
                break

            action = get_next_action(
                goal,
                page_text
            )

            print()
            print("LLM DECISION:")
            print(action)

            execute_action(page, action)

            if action.get("action") == "finish":
                print()
                print("Agent finished.")
                break

        else:
            print()
            print("FAILED: Maximum step count reached.")

        input("\nPress Enter to close the browser...")

        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--goal",
        required=True
    )

    args = parser.parse_args()

    run_agent(args.goal)