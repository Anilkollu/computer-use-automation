# Computer-Use Automation

A focused end-to-end implementation of an LLM-driven computer-use system that discovers a workflow through a live UI, records the successful workflow as a reusable capability, and deterministically replays that capability without an LLM.

## What this demonstrates

The system implements the following flow:

```text
Natural-language goal
        |
        v
LLM-driven discovery
        |
        v
Playwright browser interaction
        |
        v
Mock banking application
        |
        v
Successful payment
        |
        v
Versioned capability artifact
        |
        v
Deterministic replay
        |
        v
LLM calls: 0
```

The replay path also handles:

* successful payments
* expected business outcomes
* recoverable errors with retry
* hard failures
* human-required intervention
* checkpoint verification
* structured event logging

## Architecture

```text
agent/
    runner.py
    llm.py

artifact/
    schema.py
    builder.py

replay/
    engine.py

safety/
    policy.py

target-app/
    login.html
    dashboard.html
    payment.html
    app.js

artifacts/
    submit-payment-v1.json

evidence/
    discovery-success.log
    replay-success.log
    business-error.log
    recoverable-error.log
    hard-failure.log
    human-handoff.log
    replay-events.jsonl

run_replay.py
start_mock_app.py
REPORT.md
requirements.txt
```

## Setup

Python 3.11+ is recommended.

Install dependencies:

```powershell
pip install -r requirements.txt
```

Install the Playwright browser:

```powershell
python -m playwright install chromium
```

Set the Gemini API key (PowerShell):

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Or on macOS / Linux (bash):

```bash
pip install -r requirements.txt
python -m playwright install chromium
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

The API key is read from the environment and is not stored in the capability artifact.

## Start the mock application

From the repository root:

```powershell
python start_mock_app.py
```

Keep that terminal running.

The application is available at:

```text
http://127.0.0.1:3000/login.html
```

## Discovery run

In a second PowerShell terminal:

```powershell
python -m agent.runner --goal "Submit a $500 payment from account 12345 to account 67890"
```

The agent observes the live UI, asks the LLM to decide the next action, and executes the action through Playwright.

A successful run creates:

```text
artifacts/submit-payment-v1.json
```

## Deterministic replay

Run:

```powershell
python run_replay.py
```

Replay executes the saved artifact without asking the LLM to make decisions.

A successful replay reports:

```text
REPLAY SUCCESS
LLM calls: 0
```

## Replay scenarios

### Normal success

```powershell
python run_replay.py
```

### Business outcome

```powershell
python run_replay.py --scenario business-error
```

Expected result:

```text
BUSINESS_OUTCOME
Reason: INSUFFICIENT_FUNDS
```

### Recoverable error

```powershell
python run_replay.py --scenario recoverable-error
```

Expected behavior:

```text
RECOVERABLE_ERROR
Retrying Submit Payment...
Retry succeeded
```

### Hard failure

```powershell
python run_replay.py --scenario hard-failure
```

Expected result:

```text
HARD_FAILURE
Reason: PERMISSION_DENIED
```

### Human handoff

```powershell
python run_replay.py --scenario human-required
```

Expected behavior:

```text
HUMAN_REQUIRED
```

The browser session remains active. The human intervention occurs in the same session and the replay then resumes.

## Safety

The safety policy allowlists the local mock-bank origin and rejects non-allowlisted origins.

Example:

```powershell
python -c "from safety.policy import validate_url; validate_url('http://127.0.0.1:3000/login.html'); print('PASS: mock bank allowed')"
```

A non-allowlisted origin is rejected.

No real banking credentials, cus
