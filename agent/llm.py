import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise SystemExit(
        "GEMINI_API_KEY is not set. "
        "Create a .env file with GEMINI_API_KEY=YOUR_KEY."
    )

client = genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are a computer-use agent operating a small mock banking web application.

Choose exactly ONE browser action at a time.

Allowed actions:
- click
- fill
- finish

Return ONLY valid JSON.

CLICK:
{
  "action": "click",
  "target": "exact visible button or link name"
}

FILL:
{
  "action": "fill",
  "target": "exact visible field label",
  "value": "value"
}

FINISH:
{
  "action": "finish"
}

MOCK BANK LOGIN:
Username = demo
Password = demo

LOGIN RULES:
- If username is empty, fill Username with demo.
- If password is empty, fill Password with demo.
- If both login fields already contain values, click Login.
- Never fill a login field that already contains its required value.

PAYMENT RULES:
- After login, click Payments.
- Fill From Account with the source account from the goal.
- Fill To Account with the destination account from the goal.
- Fill Amount with the amount from the goal.
- Never fill a payment field that already contains the requested value.
- Once all three payment fields contain their requested values, click Submit Payment.
- When PAYMENT SUCCESSFUL is visible, finish.

Choose exactly ONE action.
Never repeat a completed action.
"""


def get_next_action(goal: str, page_text: str, values: dict) -> dict:
    from_account = str(values["from_account"])
    to_account = str(values["to_account"])
    amount = str(values["amount"])

    user_prompt = f"""
USER GOAL:
{goal}

CURRENT PAGE STATE:
{page_text}

IMPORTANT:
The CURRENT PAGE STATE is authoritative.

Payment values from the goal:
- From Account = {from_account}
- To Account = {to_account}
- Amount = {amount}

The page uses these field names:
- FIELD fromAccount
- FIELD toAccount
- FIELD amount

PAYMENT DECISION ORDER:

1. If FIELD fromAccount is empty:
   return:
   {{"action":"fill","target":"From Account","value":"{from_account}"}}

2. Otherwise, if FIELD toAccount is empty:
   return:
   {{"action":"fill","target":"To Account","value":"{to_account}"}}

3. Otherwise, if FIELD amount is empty:
   return:
   {{"action":"fill","target":"Amount","value":"{amount}"}}

4. Otherwise, all payment fields are already filled.
   Return:
   {{"action":"click","target":"Submit Payment"}}

CRITICAL:
If the page says:

FIELD amount: {amount}

then DO NOT fill Amount again.
Click Submit Payment instead.

LOGIN DECISION ORDER:

If the page is the login page:

1. If username is empty:
   fill Username with demo.

2. Otherwise, if password is empty:
   fill Password with demo.

3. Otherwise:
   click Login.

DASHBOARD:
If the page is the dashboard and Payments is visible:
click Payments.

SUCCESS:
If PAYMENT SUCCESSFUL is visible:
finish.

Return exactly ONE JSON object.
Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            SYSTEM_PROMPT,
            user_prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(
                thinking_level="low"
            )
        )
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:
        action = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {text}"
        )

    if not isinstance(action, dict):
        raise RuntimeError(
            f"Gemini response was not a JSON object: {action}"
        )

    if action.get("action") not in {"click", "fill", "finish"}:
        raise RuntimeError(
            f"Unsupported LLM action: {action}"
        )

    return action