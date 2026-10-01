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

## Environment Configuration

Create a local `.env` file in the repository root:

```text
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

The application loads the API key from `.env` using `python-dotenv`.

The `.env` file is excluded from Git and must never be committed.

The API key is used only for the LLM-driven discovery run. Deterministic replay does not require an LLM or API key.

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

The banking application is a local mock application created only for this assignment.

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

The artifact contains the reusable workflow, inputs, ordered UI actions, outputs, checkpoint, and capability version.

The API key is not stored in the capability artifact.

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

This demonstrates that the workflow discovered by the LLM can subsequently be executed deterministically without another LLM decision-making call.

## Replay scenarios

### Normal success

```powershell
python run_replay.py
```

Expected result:

```text
REPLAY SUCCESS
LLM calls: 0
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

This represents an expected business outcome rather than an automation failure.

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

The replay retries the blocked operation and continues when the retry succeeds.

### Hard failure

```powershell
python run_replay.py --scenario hard-failure
```

Expected result:

```text
HARD_FAILURE
Reason: PERMISSION_DENIED
```

The automation stops when the operation cannot safely continue.

### Human handoff

```powershell
python run_replay.py --scenario human-required
```

Expected behavior:

```text
HUMAN_REQUIRED
```

The browser session remains active. The human intervention occurs in the same session and the replay then resumes.

After the intervention is completed, the workflow continues and can reach:

```text
REPLAY SUCCESS
LLM calls: 0
```

## Safety

The safety policy allowlists the local mock-bank origin and rejects non-allowlisted origins.

Example:

```powershell
python -c "from safety.policy import validate_url; validate_url('http://127.0.0.1:3000/login.html'); print('PASS: mock bank allowed')"
```

A non-allowlisted origin is rejected.

No real banking credentials, customer data, or financial systems are used. The banking application is a local mock application created only for this assignment.

The project also avoids storing passwords in the reusable capability artifact.

## Evidence

The `evidence/` directory contains execution logs demonstrating the implemented workflows:

* `discovery-success.log` — successful LLM-driven discovery
* `replay-success.log` — deterministic replay with zero LLM calls
* `business-error.log` — expected business outcome
* `recoverable-error.log` — recoverable failure and retry
* `hard-failure.log` — non-recoverable failure
* `human-handoff.log` — human intervention and resume
* `replay-events.jsonl` — structured replay events

These files provide execution evidence for the main workflow and the different replay outcomes.

## End-to-End Demo

1. Start the mock banking application.
2. Run the natural-language discovery workflow.
3. The LLM drives the browser through Playwright.
4. A successful workflow is saved as a versioned capability artifact.
5. Run deterministic replay from the saved artifact.
6. Verify that replay reports `LLM calls: 0`.
7. Run the business-error, recoverable-error, hard-failure, and human-required scenarios.
8. Review the corresponding evidence logs.

The key property demonstrated by the project is that a workflow discovered using an LLM can be saved as a reusable capability and subsequently executed deterministically without another LLM decision-making call.

## Project Report

Additional design and implementation details are provided in:

```text
REPORT.md
```

The report covers the architecture, capability artifact, determinism and error handling, heterogeneity and multi-tenant considerations, escalation and handoff, safety, and implementation trade-offs.

