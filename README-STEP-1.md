# Step 1 — Mock Banking UI

This is the intentionally small local target application for the Computer-Use Automation assignment.

## What it supports

1. Login
2. Open Dashboard
3. Open Payments
4. Fill From Account
5. Fill To Account
6. Fill Amount
7. Submit Payment
8. Display a fake successful transaction result

There is no Spring Boot, Kafka, database, real banking service, or external banking credential.

## Requirements

- Python 3.10+
- A browser

## Start

From this directory:

```bash
python start_mock_app.py
```

Then open:

```text
http://127.0.0.1:3000/login.html
```

Use any fake username and password.

Example:

```text
Username: demo
Password: demo
From Account: 12345
To Account: 67890
Amount: 500
```

## Expected flow

```text
Login
  -> Dashboard
  -> Payments
  -> Fill payment form
  -> Submit Payment
  -> PAYMENT SUCCESSFUL
```

This frontend-only mock exists so the later Python + Playwright agent has a real browser surface to operate.
