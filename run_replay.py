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

            # Store the scenario in the browser session.
            # This avoids reloading payment.html later and losing
            # the values already entered into the form.
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
                    execute_step(page, step, inputs)

                    print("  ✓ Step completed")

                    # Log the action without recording sensitive values.
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

                # After submitting the payment, inspect the result.
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

            # CHECKPOINT
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

            # OUTPUTS
            outputs = extract_outputs(page)

            print()
            print("OUTPUTS")
            print(f"Transaction ID: {outputs['transactionId']}")
            print(f"Status: {outputs['status']}")

            # SUCCESS
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