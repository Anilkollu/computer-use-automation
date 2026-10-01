import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


import argparse

from playwright.sync_api import sync_playwright

from replay.engine import (
    ReplayError,
    load_artifact,
    execute_step,
    verify_checkpoint,
    extract_outputs,
)

from observability.logger import log_event

from safety.policy import (
    SafetyError,
    validate_action,
    validate_url,
)

BASE_URL = "http://127.0.0.1:3000"


def run_replay(
    artifact_path: str,
    from_account: str,
    to_account: str,
    amount: float,
    scenario: str,
):
    artifact = load_artifact(artifact_path)

    inputs = {
        "username": "demo",
        "password": "demo",
        "fromAccount": from_account,
        "toAccount": to_account,
        "amount": amount,
    }

    print()
    print("================================")
    print("DETERMINISTIC REPLAY")
    print("================================")
    print(f"Capability: {artifact['capability_id']}")
    print(f"Version: {artifact['capability_version']}")
    print("LLM calls: 0")

    if scenario != "normal":
        print(f"Scenario: {scenario}")

    log_event(
        "replay_started",
        capability=artifact["capability_id"],
        version=artifact["capability_version"],
        scenario=scenario,
        llm_calls=0,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print()
            print("Opening Mock Bank...")

            page.goto(f"{BASE_URL}/login.html")

            try:
                validate_url(page.url)
            except SafetyError as exc:
                print(f"SAFETY BLOCKED: {exc}")
                return

            if scenario != "normal":
                page.evaluate(
                    """scenario => sessionStorage.setItem("scenario", scenario)""",
                    scenario,
                )

            steps = artifact["steps"]

            for index, step in enumerate(steps, start=1):
                print()
                print(f"STEP {index}/{len(steps)}")

                try:
                    try:
                        validate_action(step)
                    except SafetyError as exc:
                        print()
                        print(f"SAFETY BLOCKED at step {index}: {exc}")

                        log_event(
                            "safety_blocked",
                            step=index,
                            reason=str(exc),
                            outcome="SAFETY_BLOCKED",
                        )

                        return

                    execute_step(page, step, inputs)

                    print("  ✓ Step completed")

                    log_event(
                        "step_completed",
                        step=index,
                        action=step["action"],
                        target=step["target"],
                    )

                except Exception as exc:
                    print()
                    print("HARD_FAILURE")
                    print(f"Step: {index}")
                    print(f"Action: {step['action']}")
                    print(f"Reason: {exc}")

                    log_event(
                        "hard_failure",
                        step=index,
                        action=step["action"],
                        reason=str(exc),
                        outcome="HARD_FAILURE",
                    )

                    return

                if (
                    step["action"] == "click"
                    and step["target"].get("name") == "Submit Payment"
                ):
                    page.wait_for_timeout(300)

                    result_text = page.locator("#result").inner_text()

                    print()
                    print("PAYMENT RESULT:")
                    print(result_text)

                    # BUSINESS OUTCOME
                    if "INSUFFICIENT FUNDS" in result_text:
                        print()
                        print("================================")
                        print("BUSINESS_OUTCOME")
                        print("Reason: INSUFFICIENT_FUNDS")
                        print("Automation completed with a business outcome.")
                        print("================================")

                        log_event(
                            "business_outcome",
                            reason="INSUFFICIENT_FUNDS",
                            outcome="BUSINESS_OUTCOME",
                        )

                        return

                    # HARD FAILURE
                    if "PERMISSION DENIED" in result_text:
                        print()
                        print("================================")
                        print("HARD_FAILURE")
                        print("Reason: PERMISSION_DENIED")
                        print("Automation stopped.")
                        print("================================")

                        log_event(
                            "hard_failure",
                            reason="PERMISSION_DENIED",
                            outcome="HARD_FAILURE",
                        )

                        return

                    # HUMAN REQUIRED
                    if "HUMAN APPROVAL REQUIRED" in result_text:
                        print()
                        print("================================")
                        print("HUMAN_REQUIRED")
                        print("Reason: MANUAL_APPROVAL_REQUIRED")
                        print("The automation is paused for human intervention.")
                        print("Browser session remains active.")
                        print("================================")

                        log_event(
                            "human_handoff",
                            reason="MANUAL_APPROVAL_REQUIRED",
                            step=index,
                            context=result_text,
                        )

                        input(
                            "\nThe browser session is live and paused. "
                            "In the browser window, click the Approve Payment "
                            "button to approve, then press Enter here to resume..."
                        )

                        log_event(
                            "human_resumed",
                            step=index,
                        )

                        print()
                        print("Resuming automation in the same browser session...")

                        # The human acted in the live session. Verify what the
                        # page actually shows now instead of assuming success.
                        page.wait_for_timeout(300)

                        resumed_result = page.locator("#result").inner_text()

                        page.wait_for_timeout(300)

                        resumed_result = page.locator("#result").inner_text()

                        print()
                        print("POST-HUMAN RESULT:")
                        print(resumed_result)

                        if "PAYMENT SUCCESSFUL" not in resumed_result:
                            print()
                            print("HARD_FAILURE")
                            print("Reason: Human handoff did not resolve the operation.")

                            log_event(
                                "hard_failure",
                                reason="HUMAN_HANDOFF_FAILED",
                                outcome="HARD_FAILURE",
                            )

                            return

                        print()
                        print("✓ Human intervention resolved the blocked operation.")

                    # RECOVERABLE ERROR
                    if "SERVICE TEMPORARILY UNAVAILABLE" in result_text:
                        print()
                        print("RECOVERABLE_ERROR")
                        print("Reason: SERVICE_TEMPORARILY_UNAVAILABLE")

                        log_event(
                            "recoverable_error",
                            reason="SERVICE_TEMPORARILY_UNAVAILABLE",
                        )

                        print("Retrying Submit Payment...")

                        page.get_by_role(
                            "button",
                            name="Submit Payment",
                        ).click()

                        page.wait_for_timeout(300)

                        retry_result = page.locator("#result").inner_text()

                        print()
                        print("RETRY RESULT:")
                        print(retry_result)

                        if "PAYMENT SUCCESSFUL" not in retry_result:
                            print()
                            print("HARD_FAILURE")
                            print("Retry did not recover the operation.")

                            log_event(
                                "hard_failure",
                                reason="RETRY_FAILED",
                                outcome="HARD_FAILURE",
                            )

                            return

                        print()
                        print("✓ Retry succeeded")

                        log_event(
                            "retry_succeeded",
                            reason="SERVICE_TEMPORARILY_UNAVAILABLE",
                        )

            print()
            print("CHECKPOINT")

            checkpoint = artifact["checkpoint"]

            checkpoint_passed = verify_checkpoint(
                page,
                checkpoint,
            )

            if not checkpoint_passed:
                print("HARD_FAILURE")
                print("Reason: Checkpoint failed")

                log_event(
                    "hard_failure",
                    reason="CHECKPOINT_FAILED",
                    outcome="HARD_FAILURE",
                )

                return

            print("✓ Checkpoint passed")

            outputs = extract_outputs(page)

            print()
            print("OUTPUTS")
            print(f"Transaction ID: {outputs['transactionId']}")
            print(f"Status: {outputs['status']}")

            print()
            print("================================")
            print("REPLAY SUCCESS")
            print("LLM calls: 0")
            print("================================")

            log_event(
                "replay_success",
                capability=artifact["capability_id"],
                version=artifact["capability_version"],
                outputs=outputs,
                llm_calls=0,
            )

            input("\nPress Enter to close the browser...")

        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--artifact",
        default="artifacts/submit-payment-v1.json",
    )

    parser.add_argument(
        "--from-account",
        default="12345",
    )

    parser.add_argument(
        "--to-account",
        default="67890",
    )

    parser.add_argument(
        "--amount",
        type=float,
        default=500,
    )

    parser.add_argument(
        "--scenario",
        choices=[
            "normal",
            "business-error",
            "recoverable-error",
            "hard-failure",
            "human-required",
        ],
        default="normal",
    )

    args = parser.parse_args()

    try:
        run_replay(
            artifact_path=args.artifact,
            from_account=args.from_account,
            to_account=args.to_account,
            amount=args.amount,
            scenario=args.scenario,
        )

    except ReplayError as exc:
        print()
        print(f"REPLAY ERROR: {exc}")