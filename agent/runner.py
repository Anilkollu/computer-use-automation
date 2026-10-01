import argparse
import re

from playwright.sync_api import sync_playwright

from agent.llm import get_next_action
from artifact.builder import (
    build_submit_payment_artifact,
    save_artifact,
)
from safety.policy import (
    SafetyError,
    validate_action,
    validate_page,
)


BASE_URL = "http://127.0.0.1:3000"


def parse_goal(goal: str) -> dict:
    """Extract payment values from a natural-language goal.

    Understands goals like:
        "Submit a $500 payment from account 12345 to account 67890"
    Falls back to the demo defaults when the goal does not name values.
    """
    values = {
        "from_account": "12345",
        "to_account": "67890",
        "amount": "500",
    }

    from_match = re.search(r"from account (\w+)", goal, re.IGNORECASE)
    to_match = re.search(r"to account (\w+)", goal, re.IGNORECASE)

    # An explicit dollar amount ("$500"), or a number followed by a
    # money word ("500 dollars"). Never treat an account number as
    # the amount.
    dollar_match = re.search(r"\$(\d+(?:\.\d{1,2})?)", goal)
    word_match = re.search(
        r"(\d+(?:\.\d{1,2})?)\s*(?:dollar|payment|amount)",
        goal,
        re.IGNORECASE,
    )

    if from_match:
        values["from_account"] = from_match.group(1)
    if to_match:
        values["to_account"] = to_match.group(1)
    if dollar_match:
        values["amount"] = dollar_match.group(1)
    elif word_match:
        values["amount"] = word_match.group(1)

    return values


def get_page_state(page):
    state = page.locator("body").inner_text()

    inputs = page.locator("input")

    for i in range(inputs.count()):
        field = inputs.nth(i)

        try:
            label = (
                field.get_attribute("id")
                or field.get_attribute("name")
            )

            value = field.input_value()

            if label:
                state += f"\nFIELD {label}: {value}"

        except Exception:
            pass

    buttons = page.locator("button")

    for i in range(buttons.count()):
        try:
            text = buttons.nth(i).inner_text().strip()

            if text:
                state += f"\nBUTTON: {text}"

        except Exception:
            pass

    links = page.locator("a")

    for i in range(links.count()):
        try:
            text = links.nth(i).inner_text().strip()

            if text:
                state += f"\nLINK: {text}"

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
            ).click(timeout=5000)

            return {
                "action": "click",
                "target": {
                    "role": "button",
                    "name": target
                }
            }

        except Exception:
            page.get_by_role(
                "link",
                name=target
            ).click(timeout=5000)

            return {
                "action": "click",
                "target": {
                    "role": "link",
                    "name": target
                }
            }

    if action_type == "fill":
        target = action["target"]
        value = action["value"]

        print(f"  ACTION: fill -> {target}")

        page.get_by_label(target).fill(value)

        return {
            "action": "fill",
            "target": {
                "label": target
            },
            "value": value
        }

    if action_type == "finish":
        print("  ACTION: finish")

        return {
            "action": "finish",
            "target": {}
        }

    raise RuntimeError(
        f"Unsupported action: {action_type}"
    )


def run_agent(goal):
    values = parse_goal(goal)

    print(f"Goal: {goal}")
    print(f"Parsed values: {values}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        print("Opening Mock Bank...")
        page.goto(f"{BASE_URL}/login.html")

        try:
            validate_page(page)
        except SafetyError as exc:
            print(f"SAFETY BLOCKED: {exc}")
            browser.close()
            return

        max_steps = 15

        recorded_actions = []

        for step in range(1, max_steps + 1):
            print()
            print(f"========== STEP {step} ==========")

            page_text = get_page_state(page)

            print("CURRENT PAGE:")
            print(page_text)

            # -----------------------------------------
            # SUCCESS CHECK
            # -----------------------------------------
            if "PAYMENT SUCCESSFUL" in page_text:
                print()
                print("SUCCESS: Goal completed.")

                artifact = build_submit_payment_artifact(
                    recorded_actions
                )

                artifact_path = save_artifact(artifact)

                print()
                print(f"ARTIFACT SAVED: {artifact_path}")
                break

            # -----------------------------------------
            # LLM DECIDES THE NEXT ACTION
            # -----------------------------------------
            try:
                validate_page(page)

                action = get_next_action(
                    goal,
                    page_text,
                    values,
                )

                validate_action(action)
            except SafetyError as exc:
                print()
                print(f"SAFETY BLOCKED: {exc}")
                break

            print()
            print("DECISION:")
            print(action)

            recorded_action = execute_action(
                page,
                action
            )

            if action.get("action") != "finish":
                recorded_actions.append(recorded_action)

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
