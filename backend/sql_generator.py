import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import vector_store
from prompt_builder import build_prompt

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_sql(question: str, schema: dict, previous_sql: str = None, error_message: str = None) -> dict:
    """Call Gemini to generate SQL from natural language."""
    prompt = build_prompt(question, schema)
    
    if previous_sql and error_message:
        prompt += f"\n\nPREVIOUS ATTEMPT FAILED:\nSQL: {previous_sql}\nError: {error_message}\nFix the query so it executes successfully."
    elif previous_sql:
        prompt += f"\n\nCONVERSATIONAL CONTEXT - PREVIOUS SQL GENERATED:\n{previous_sql}\n(Use this for context if the user's new question is a follow-up, such as 'what about the top 10 instead?')"

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "sql": "",
            "explanation": "Failed to parse LLM response",
            "confidence": 0.0,
            "tables_used": [],
            "ambiguous": False,
            "clarification_needed": ""
        }

    return result


if __name__ == "__main__":
    import json
    with open("schema.json") as f:
        schema = json.load(f)

    q = "What are the top 5 selling artists?"
    print(f"Question: {q}")
    result = generate_sql(q, schema)
    print(json.dumps(result, indent=2))
