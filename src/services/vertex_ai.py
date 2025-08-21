import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import re
from config import GCP_PROJECT_ID, GCP_LOCATION, GCP_MODEL_NAME

_is_vertex_initialized = False

def init_vertex_ai():
    """Initializes the Vertex AI client if not already initialized."""
    global _is_vertex_initialized
    if not _is_vertex_initialized:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        _is_vertex_initialized = True

def parse_expense_with_llm(text: str) -> dict | None:
    """
    Uses a Large Language Model to parse user intent from text.
    Can parse 'add_expense' or 'get_report' intents.
    Returns a dictionary with the parsed data or None on failure.
    """
    response_text = ""
    try:
        init_vertex_ai()

        # Extended few-shot prompt with intents.
        # The date for the examples is assumed to be 2025-08-21.
        # Double braces {{...}} are used to escape the JSON for the f-string.
        prompt = f"""You are an intelligent assistant for a voice-controlled expense tracker.
Your task is to interpret a transcribed voice message and determine the user's intent.
The two possible intents are 'add_expense' and 'get_report'.
Your response MUST be a valid JSON object. Do not add any text before or after the JSON.

---
USER:
запиши, пожалуйста, расход 250 рублей на кофе

MODEL:
{{
  "intent": "add_expense",
  "amount": 250.0,
  "category": "кофе",
  "confirmation_message": "Вы имели в виду расход 250.00 на 'кофе' сегодняшним числом? Я правильно понял?"
}}
---
USER:
Так, напиши расход 500 тысяч на ужин.

MODEL:
{{
  "intent": "add_expense",
  "amount": 500000.0,
  "category": "ужин",
  "confirmation_message": "Вы имели в виду расход 500000.00 на 'ужин' сегодняшним числом? Я правильно понял?"
}}
---
USER:
какие были расходы за прошлую неделю

MODEL:
{{
  "intent": "get_report",
  "start_date": "2025-08-11",
  "end_date": "2025-08-17"
}}
---
USER:
покажи отчет за этот месяц

MODEL:
{{
  "intent": "get_report",
  "start_date": "2025-08-01",
  "end_date": "2025-08-21"
}}
---
USER:
{text}

MODEL:
"""

        model = GenerativeModel(GCP_MODEL_NAME)
        response = model.generate_content(prompt)

        response_text = response.text

        # This is the robust way to get the JSON.
        # It looks for a JSON block optionally wrapped in ```json ... ```
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if match:
            # If markdown block is found, extract the JSON part from group 1
            json_str = match.group(1)
        else:
            # If no markdown block is found, assume the whole response is the JSON
            json_str = response_text

        parsed_response = json.loads(json_str)

        # Check for a valid intent instead of just 'amount'
        if parsed_response and parsed_response.get('intent'):
            return parsed_response
        else:
            return None

    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Original text from LLM: {response_text}")
        return None
