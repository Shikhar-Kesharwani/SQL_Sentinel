import os
import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Load once at module level — small model, fast
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def back_translate_sql(sql: str) -> str:
    """Ask LLM: what question does this SQL answer?"""
    prompt = f"""Given this SQL query, describe in one sentence what question it answers.
Be specific about filters, groupings, and what is being counted or selected.

SQL:
{sql}

Answer in one sentence:"""

    response = model.generate_content(prompt)
    return response.text.strip()


def semantic_similarity(text1: str, text2: str) -> float:
    """Cosine similarity between two texts using sentence embeddings."""
    emb1 = embedder.encode(text1, convert_to_tensor=True)
    emb2 = embedder.encode(text2, convert_to_tensor=True)
    score = util.cos_sim(emb1, emb2).item()
    return round(score, 4)


def sanity_check_results(columns: list, rows: list, question: str) -> dict:
    """Check if results make sense."""
    issues = []
    passed = True

    # Check 1: Empty results
    if len(rows) == 0:
        issues.append("Query returned 0 rows — may indicate a bad JOIN or wrong filter")
        passed = False

    # Check 2: All NULLs in first column
    if rows:
        first_col_vals = [r[0] for r in rows if r]
        null_ratio = sum(1 for v in first_col_vals if v is None) / len(first_col_vals)
        if null_ratio > 0.8:
            issues.append(f"First column is {null_ratio*100:.0f}% NULL — likely a bad JOIN")
            passed = False

    # Check 3: Negative counts
    if rows and columns:
        count_cols = [i for i, c in enumerate(columns) if "count" in c.lower()]
        for col_idx in count_cols:
            for row in rows:
                if col_idx < len(row) and row[col_idx] is not None:
                    if isinstance(row[col_idx], (int, float)) and row[col_idx] < 0:
                        issues.append(f"Column '{columns[col_idx]}' has negative count — impossible value")
                        passed = False

    # Check 4: Implausibly large revenue
    if rows and columns:
        revenue_cols = [i for i, c in enumerate(columns)
                        if any(k in c.lower() for k in ["revenue", "total", "amount", "price"])]
        for col_idx in revenue_cols:
            for row in rows:
                if col_idx < len(row) and row[col_idx] is not None:
                    if isinstance(row[col_idx], (int, float)) and row[col_idx] > 1_000_000:
                        issues.append(
                            f"Column '{columns[col_idx]}' has suspiciously large value: {row[col_idx]}"
                        )

    return {"passed": passed, "issues": issues}


def compute_confidence(
    llm_confidence: float,
    back_translation_sim: float,
    sanity_passed: bool,
    execution_success: bool
) -> float:
    """
    Composite confidence score:
    - 35% LLM self-reported confidence
    - 40% back-translation semantic similarity
    - 15% sanity checks
    - 10% execution success
    """
    sanity_score = 1.0 if sanity_passed else 0.0
    exec_score = 1.0 if execution_success else 0.0

    score = (
        0.35 * llm_confidence +
        0.40 * back_translation_sim +
        0.15 * sanity_score +
        0.10 * exec_score
    )
    return round(min(max(score, 0.0), 1.0), 3)


def detect_hallucination(
    question: str,
    sql: str,
    llm_confidence: float,
    execution_result: dict
) -> dict:
    """Full hallucination detection pipeline."""

    # Step 1: Back-translation
    back_translated = back_translate_sql(sql)
    similarity = semantic_similarity(question, back_translated)

    # Step 2: Sanity checks on results
    sanity = sanity_check_results(
        execution_result.get("columns", []),
        execution_result.get("rows", []),
        question
    )

    # Step 3: Composite confidence
    final_confidence = compute_confidence(
        llm_confidence=llm_confidence,
        back_translation_sim=similarity,
        sanity_passed=sanity["passed"],
        execution_success=execution_result.get("success", False)
    )

    # Step 4: Flag if suspicious
    is_hallucination = (
        final_confidence < 0.5 or
        similarity < 0.4 or
        not sanity["passed"]
    )

    return {
        "back_translated_question": back_translated,
        "semantic_similarity": similarity,
        "sanity_check": sanity,
        "final_confidence": final_confidence,
        "is_hallucination": is_hallucination,
        "warning": "Low confidence — please verify this result" if is_hallucination else None
    }


if __name__ == "__main__":
    # Quick test
    question = "What are the top 5 artists by album count?"
    sql = "SELECT ar.Name, COUNT(al.AlbumId) as albums FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId GROUP BY ar.Name ORDER BY albums DESC LIMIT 5"

    result = detect_hallucination(
        question=question,
        sql=sql,
        llm_confidence=0.9,
        execution_result={
            "success": True,
            "columns": ["Name", "albums"],
            "rows": [["Iron Maiden", 21], ["Led Zeppelin", 14]],
            "row_count": 2
        }
    )
    print(json.dumps(result, indent=2))
