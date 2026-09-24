import json
import os

from google import genai
from google.genai import types


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


SYSTEM_PROMPT = """
You are a computer-use agent operating a small mock banking web application.

Your job is to accomplish the user's goal by choosing exactly ONE browser action at a time.

Allowed actions:

1. click
2. fill
3. finish

Return ONLY valid JSON.

For click:
{
  "action": "click",
  "target": "exact visible button or link name"
}

For fill:
{
  "action": "fill",
  "target": "exact visible field label",
  "value": "value"
}

For finish:
{
  "action": "finish"
}

MOCK BANK LOGIN:
Username = demo
Password = demo

IMPORTANT RULES:

- Look carefully at CURRENT PAGE and FIELD values.
- Do not repeat an action that has already been completed.
- If Username already contains "demo", do NOT fill Username again.
- If Username is empty, fill Username with "demo".
- If Password is empty, fill Password with "demo".
- After both login fields are filled, click Login.
- After login, click Payments.
- Then fill the payment fields using the user's goal.
- Do not use payment account numbers as login credentials.
- Do not invent controls.
- Choose exactly ONE action.
- Do not finish until PAYMENT SUCCESSFUL is visible.
- Never expose or save passwords in artifacts or logs.
"""





def get_next_action(goal: str, page_text: str) -> dict:
    user_prompt = f"""
USER GOAL:
{goal}

CURRENT PAGE:
{page_text}

Choose the next action based ONLY on the CURRENT PAGE.

If the login page is visible:
- Fill Username with "demo"
- Fill Password with "demo"
- Click Login

After login:
- Click Payments
- Fill From Account with the from-account from the goal
- Fill To Account with the to-account from the goal
- Fill Amount with the amount from the goal
- Click Submit Payment

If PAYMENT SUCCESSFUL is visible:
return:
{{"action": "finish"}}

Return exactly ONE JSON action.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            SYSTEM_PROMPT,
            user_prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
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
