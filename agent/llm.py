import json
import os

from google import genai


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


SYSTEM_PROMPT = """
You are a computer-use agent operating a small mock banking web application.

Your job is to accomplish the user's goal by choosing one browser action at a time.

You may ONLY choose these actions:

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
  "target": "exact field label",
  "value": "value"
}

For finish:
{
  "action": "finish"
}

Rules:
- Use the current page information to decide the next action.
- Do not invent controls that are not visible.
- Complete the user's requested payment.
- Use the values provided in the user's goal.
- Never expose or save passwords in logs or artifacts.
- Finish only after the payment success message is visible.
- Choose exactly one action at a time.
"""


def get_next_action(goal: str, page_text: str) -> dict:

    user_prompt = f"""
USER GOAL:
{goal}

CURRENT PAGE:
{page_text}

Choose exactly ONE next browser action.

Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            SYSTEM_PROMPT,
            user_prompt
        ],
        config={
            "temperature": 0
        }
    )

    text = response.text.strip()

    # Handle accidental markdown code fences.
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {text}"
        )