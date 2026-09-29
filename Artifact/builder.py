import json
from pathlib import Path

from artifact.schema import CapabilityArtifact


ARTIFACTS_DIR = Path("artifacts")


def parameterize_action(action: dict) -> dict:
    result = {
        "action": action["action"],
        "target": action["target"],
    }

    if action["action"] != "fill":
        return result

    target = action["target"].get("label")
    value = action.get("value")

    if target == "Username":
        result["value"] = "{{username}}"

    elif target == "Password":
        result["value"] = "{{password}}"

    elif target == "From Account":
        result["value"] = "{{fromAccount}}"

    elif target == "To Account":
        result["value"] = "{{toAccount}}"

    elif target == "Amount":
        result["value"] = "{{amount}}"

    else:
        result["value"] = value

    return result


def build_submit_payment_artifact(
    recorded_actions: list[dict]
) -> CapabilityArtifact:

    steps = [
        parameterize_action(action)
        for action in recorded_actions
    ]

    artifact = CapabilityArtifact(
        schema_version="1.0",

        capability_id="submit-payment",

        capability_version=1,

        inputs={
            "fromAccount": {
                "type": "string",
                "description": "Source account number"
            },
            "toAccount": {
                "type": "string",
                "description": "Destination account number"
            },
            "amount": {
                "type": "number",
                "description": "Payment amount"
            },
            "username": {
                "type": "string",
                "secret": "true",
                "description": "Application username"
            },
            "password": {
                "type": "string",
                "secret": "true",
                "description": "Application password"
            }
        },

        steps=steps,

        outputs={
            "transactionId": {
                "type": "string",
                "description": "Generated payment transaction ID"
            },
            "status": {
                "type": "string",
                "description": "Payment completion status"
            }
        },

        checkpoint={
            "type": "text",
            "contains": "PAYMENT SUCCESSFUL"
        }
    )

    return artifact


def save_artifact(
    artifact: CapabilityArtifact
) -> Path:

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        ARTIFACTS_DIR /
        "submit-payment-v1.json"
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            artifact.to_dict(),
            file,
            indent=2
        )

    return path