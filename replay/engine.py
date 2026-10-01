import json
import re
from pathlib import Path

from playwright.sync_api import Page


class ReplayError(Exception):
    pass


def load_artifact(path: str) -> dict:
    artifact_path = Path(path)

    if not artifact_path.exists():
        raise ReplayError(
            f"Artifact not found: {artifact_path}"
        )

    with artifact_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def resolve_value(
    value,
    inputs: dict
):
    if not isinstance(value, str):
        return value

    pattern = r"^\{\{([^}]+)\}\}$"

    match = re.match(pattern, value)

    if not match:
        return value

    parameter_name = match.group(1)

    if parameter_name not in inputs:
        raise ReplayError(
            f"Missing replay input: {parameter_name}"
        )

    return inputs[parameter_name]


def execute_step(
    page: Page,
    step: dict,
    inputs: dict
):
    action = step["action"]
    target = step["target"]

    if action == "fill":

        label = target["label"]

        value = resolve_value(
            step["value"],
            inputs
        )

        print(
            f"  FILL: {label}"
        )

        page.get_by_label(label).fill(
            str(value)
        )

        return

    if action == "click":

        role = target["role"]
        name = target["name"]

        print(
            f"  CLICK: {role} -> {name}"
        )

        page.get_by_role(
            role,
            name=name
        ).click()

        return

    raise ReplayError(
        f"Unsupported replay action: {action}"
    )


def extract_outputs(
    page: Page
) -> dict:

    result_text = page.locator(
        "#result"
    ).inner_text()

    transaction_match = re.search(
        r"Transaction ID:\s*(TXN-\d+)",
        result_text
    )

    status_match = re.search(
        r"Status:\s*(\w+)",
        result_text
    )

    return {
        "transactionId": (
            transaction_match.group(1)
            if transaction_match
            else None
        ),
        "status": (
            status_match.group(1)
            if status_match
            else None
        )
    }


def verify_checkpoint(
    page: Page,
    checkpoint: dict
) -> bool:

    checkpoint_type = checkpoint["type"]

    if checkpoint_type != "text":
        raise ReplayError(
            f"Unsupported checkpoint type: "
            f"{checkpoint_type}"
        )

    expected_text = checkpoint["contains"]

    page_text = page.locator(
        "body"
    ).inner_text()

    return expected_text in page_text
