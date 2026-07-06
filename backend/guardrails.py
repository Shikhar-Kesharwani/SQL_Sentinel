import re
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from db_config import get_db_path

LOG_PATH = Path(__file__).parent / "blocked_queries.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.WARNING,
    format="%(asctime)s | %(message)s"
)

# DDL and DML keywords that must never appear
BLOCKED_KEYWORDS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
    r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bREPLACE\b",
    r"\bMERGE\b", r"\bUPSERT\b", r"\bGRANT\b", r"\bREVOKE\b",
    r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b"
]

MAX_SUBQUERY_DEPTH = 3
MAX_ROWS_WITHOUT_LIMIT = 10000


class GuardrailViolation(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def check_destructive_keywords(sql: str) -> None:
    sql_upper = sql.upper()
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, sql_upper):
            keyword = pattern.replace(r"\b", "").replace("\\b", "")
            raise GuardrailViolation(
                f"Blocked: query contains forbidden keyword '{keyword}'"
            )


def check_must_be_select(sql: str) -> None:
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
        raise GuardrailViolation(
            "Blocked: only SELECT (and WITH...SELECT) queries are allowed"
        )


def check_subquery_depth(sql: str) -> None:
    depth = 0
    max_depth = 0
    for char in sql:
        if char == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ")":
            depth -= 1
    if max_depth > MAX_SUBQUERY_DEPTH:
        raise GuardrailViolation(
            f"Blocked: query nesting depth {max_depth} exceeds max {MAX_SUBQUERY_DEPTH}"
        )


def check_has_limit(sql: str) -> None:
    """Warn if no LIMIT clause present on non-aggregation queries."""
    sql_upper = sql.upper()
    has_limit = "LIMIT" in sql_upper
    has_count = "COUNT(" in sql_upper
    has_sum = "SUM(" in sql_upper
    has_avg = "AVG(" in sql_upper

    is_aggregation = has_count or has_sum or has_avg

    if not has_limit and not is_aggregation:
        raise GuardrailViolation(
            "Blocked: query has no LIMIT clause. Add LIMIT to prevent full table scans."
        )


def check_row_count_via_explain(sql: str) -> None:
    """Use EXPLAIN QUERY PLAN to estimate scan size."""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = cursor.fetchall()
        conn.close()

        for row in plan:
            row_str = str(row).upper()
            if "SCAN" in row_str and "LIMIT" not in sql.upper():
                # Full table scan without limit — potentially dangerous
                pass  # Already caught by check_has_limit above
    except Exception:
        pass  # EXPLAIN failed — let execution layer catch it


def profile_query(sql: str) -> dict:
    """Use EXPLAIN QUERY PLAN to detect potential bottlenecks."""
    profile = {
        "is_optimized": True,
        "warnings": [],
        "plan": []
    }
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = cursor.fetchall()
        conn.close()

        for row in plan:
            # row format in SQLite EXPLAIN QUERY PLAN: (id, parent, notused, detail)
            detail = str(row[3]).upper() if len(row) > 3 else str(row).upper()
            profile["plan"].append(detail)
            
            if "SCAN TABLE" in detail or ("SCAN" in detail and "SEARCH" not in detail):
                # Check if it's scanning a small table, which is fine.
                # Since we don't have row counts here, we just warn generally if there's a SCAN without LIMIT
                if "LIMIT" not in sql.upper():
                    profile["is_optimized"] = False
                    profile["warnings"].append(f"Full table scan detected: {detail}")
                    
            if "TEMP B-TREE" in detail:
                profile["is_optimized"] = False
                profile["warnings"].append("Uses temporary B-tree for sorting/grouping (can be slow on large tables).")

    except Exception as e:
        profile["warnings"].append(f"Could not profile query: {str(e)}")

    return profile


def validate_sql(sql: str, question: str) -> dict:
    """
    Run all guardrail checks on generated SQL.
    Returns {"passed": True} or {"passed": False, "reason": "..."}
    """
    if not sql or not sql.strip():
        return {"passed": False, "reason": "Empty SQL query"}

    checks = [
        check_must_be_select,
        check_destructive_keywords,
        check_subquery_depth,
        check_has_limit,
    ]

    for check in checks:
        try:
            check(sql)
        except GuardrailViolation as e:
            # Log the blocked query
            logging.warning(f"BLOCKED | Q: {question!r} | SQL: {sql!r} | Reason: {e.reason}")
            return {"passed": False, "reason": e.reason}

    return {"passed": True}


def execute_sql_safely(sql: str) -> dict:
    """Execute SQL in a read-only context with auto-rollback."""
    try:
        conn = sqlite3.connect(get_db_path())
        conn.execute("BEGIN")  # Start transaction

        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(500)  # Hard cap: never return more than 500 rows
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        conn.rollback()  # Always rollback — we never commit
        conn.close()

        return {
            "success": True,
            "columns": columns,
            "rows": [list(r) for r in rows],
            "row_count": len(rows),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test guardrails
    test_cases = [
        ("DROP TABLE Track", "delete the track table"),
        ("DELETE FROM Customer WHERE 1=1", "remove all customers"),
        ("SELECT * FROM Track", "get all tracks"),  # No LIMIT — should block
        ("SELECT * FROM Track LIMIT 10", "get 10 tracks"),  # Should pass
        ("SELECT COUNT(*) FROM Invoice", "count invoices"),  # Aggregation — pass
    ]

    for sql, question in test_cases:
        result = validate_sql(sql, question)
        status = "✅ PASS" if result["passed"] else f"❌ BLOCKED: {result['reason']}"
        print(f"{status}\n  SQL: {sql}\n")
