import json
import os

from google import genai
from google.genai import types


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


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
- If both username and password are already filled, NEVER fill either one again.
- When both login fields contain values, the next action MUST be clicking Login.

PAYMENT RULES:
- After login, click Payments.
- Fill From Account from the user's goal.
- Fill To Account from the user's goal.
- Fill Amount from the user's goal.
- Do not use payment account numbers as login credentials.
- Do not repeat a field that already contains the requested value.
- Click Submit Payment after all payment fields are filled.
- When PAYMENT SUCCESSFUL is visible, finish.

Choose exactly ONE action.
Do not repeat completed actions.
"""


def get_next_action(goal: str, page_text: str) -> dict:

    user_prompt = f"""
USER GOAL:
{goal}

CURRENT PAGE STATE:
{page_text}

You must choose the NEXT incomplete action.

IMPORTANT:
Look carefully at the FIELD lines.

Payment fields are:
- FIELD fromAccount
- FIELD toAccount
- FIELD amount

The payment values from the user's goal are:
- From Account = 12345
- To Account = 67890
- Amount = 500

Follow this exact progression on the payment page:

1. If FIELD fromAccount is empty:
   fill From Account with 12345

2. ELSE IF FIELD toAccount is empty:
   fill To Account with 67890

3. ELSE IF FIELD amount is empty:
   fill Amount with 500

4. ELSE:
   click Submit Payment

Never fill a field that already contains a value.

LOGIN:
- Username = demo
- Password = demo

If login page:
- empty username -> fill Username with demo
- otherwise if empty password -> fill Password with demo
- otherwise -> click Login

If dashboard:
- click Payments

If PAYMENT SUCCESSFUL is visible:
- finish

Return exactly ONE JSON action.
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