from schema_extractor import schema_to_prompt_string, find_relevant_tables
import json
from pathlib import Path
import vector_store

def get_dynamic_examples(question: str, top_k: int = 3) -> str:
    """Find the most semantically similar examples using RAG."""
    relevant_contexts = vector_store.get_relevant_context(question, top_k=top_k)
    
    examples_str = ""
    for ctx in relevant_contexts:
        if ctx["type"] == "sql":
            examples_str += f"Q: {ctx['question']}\nSQL: {ctx['sql']}\n\n"
        elif ctx["type"] == "doc":
            examples_str += f"Documentation: {ctx['doc_text']}\n\n"
            
    return examples_str.strip()

def build_prompt(question: str, schema: dict) -> str:
    relevant_tables = find_relevant_tables(question, schema)
    schema_str = schema_to_prompt_string(schema, relevant_tables)
    dynamic_examples = get_dynamic_examples(question)

    prompt = f"""You are a SQL expert. Generate a SQLite SQL query for the question below.

DATABASE SCHEMA:
{schema_str}

EXAMPLE QUERIES:
{dynamic_examples}

RULES:
1. Only use SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
2. Always use LIMIT (max 1000 rows) unless counting/aggregating
3. Use table aliases for readability
4. Use proper JOINs based on foreign keys shown above
5. If the question is ambiguous, pick the most common interpretation

QUESTION: {question}

Respond ONLY with valid JSON in this exact format:
{{
  "sql": "SELECT ...",
  "explanation": "Plain English: what this query does",
  "confidence": 0.95,
  "tables_used": ["Table1", "Table2"],
  "ambiguous": false,
  "clarification_needed": "",
  "chart_config": {{
    "type": "bar", // one of: "bar", "line", "pie", "none"
    "x_key": "Name", // the column name for the x-axis or category
    "y_key": "album_count" // the column name for the y-axis or value
  }}
}}

If the question is unanswerable with the given schema, set sql to "" and explain why in explanation.
JSON response:"""

    return prompt
