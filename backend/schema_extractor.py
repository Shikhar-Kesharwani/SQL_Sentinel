import sqlite3
import json
from pathlib import Path
from db_config import get_db_path

def get_schema() -> dict:
    """Extract full schema from SQLite database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        # Get columns with types
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for col in cursor.fetchall():
            col_info = {
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "primary_key": bool(col[5])
            }
            columns.append(col_info)

        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fkeys = []
        for fk in cursor.fetchall():
            fkeys.append({
                "column": fk[3],
                "references_table": fk[2],
                "references_column": fk[4]
            })

        # Get sample values for small categorical columns
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        sample_values = {}
        if row_count < 500:
            for col in columns:
                if col["type"] in ("TEXT", "VARCHAR"):
                    cursor.execute(
                        f"SELECT DISTINCT {col['name']} FROM {table} "
                        f"WHERE {col['name']} IS NOT NULL LIMIT 5"
                    )
                    vals = [r[0] for r in cursor.fetchall()]
                    if vals:
                        sample_values[col["name"]] = vals

        schema[table] = {
            "columns": columns,
            "foreign_keys": fkeys,
            "row_count": row_count,
            "sample_values": sample_values
        }

    conn.close()
    return schema


def schema_to_prompt_string(schema: dict, relevant_tables: list = None) -> str:
    """Convert schema dict to a clean string for LLM prompts."""
    tables = relevant_tables if relevant_tables else list(schema.keys())
    lines = []

    for table in tables:
        if table not in schema:
            continue
        info = schema[table]
        lines.append(f"Table: {table} ({info['row_count']} rows)")

        for col in info["columns"]:
            pk = " [PK]" if col["primary_key"] else ""
            nn = " NOT NULL" if col["not_null"] else ""
            lines.append(f"  - {col['name']}: {col['type']}{pk}{nn}")

        for fk in info["foreign_keys"]:
            lines.append(
                f"  * FK: {fk['column']} → {fk['references_table']}.{fk['references_column']}"
            )

        if info["sample_values"]:
            for col_name, vals in info["sample_values"].items():
                lines.append(f"  ~ Sample {col_name}: {', '.join(str(v) for v in vals)}")

        lines.append("")

    return "\n".join(lines)


def find_relevant_tables(question: str, schema: dict) -> list:
    """Simple keyword match to find relevant tables."""
    question_lower = question.lower()
    relevant = []

    keyword_map = {
        "track": ["Track", "Album", "Artist"],
        "song": ["Track", "Album", "Artist"],
        "album": ["Album", "Artist"],
        "artist": ["Artist", "Album", "Track"],
        "customer": ["Customer", "Invoice", "InvoiceLine"],
        "invoice": ["Invoice", "InvoiceLine", "Customer"],
        "order": ["Invoice", "InvoiceLine"],
        "employee": ["Employee"],
        "genre": ["Genre", "Track"],
        "playlist": ["Playlist", "PlaylistTrack", "Track"],
        "revenue": ["Invoice", "InvoiceLine"],
        "sale": ["Invoice", "InvoiceLine"],
        "country": ["Customer", "Invoice"],
    }

    for keyword, tables in keyword_map.items():
        if keyword in question_lower:
            for t in tables:
                if t not in relevant:
                    relevant.append(t)

    # fallback: return all tables if nothing matched
    if not relevant:
        relevant = list(schema.keys())

    return relevant


if __name__ == "__main__":
    schema = get_schema()
    print(f"Extracted {len(schema)} tables:")
    for t, info in schema.items():
        print(f"  {t}: {len(info['columns'])} columns, {info['row_count']} rows")

    # Save schema to JSON for reuse
    with open("schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    print("\nSaved to schema.json")
