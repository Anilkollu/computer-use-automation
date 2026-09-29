import json
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("evidence")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_event(event_type: str, **data):
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        **data,
    }

    print(f"[EVENT] {json.dumps(event)}")

    log_file = LOG_DIR / "replay-events.jsonl"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")