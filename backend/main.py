import os
import sys
import traceback
from fastapi import FastAPI
import uvicorn

try:
    import json
    import sqlite3
    import uuid
    from datetime import datetime
    from pathlib import Path
    from typing import Optional
    
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    from schema_extractor import get_schema, schema_to_prompt_string
    from sql_generator import generate_sql
    from guardrails import validate_sql, execute_sql_safely, profile_query
    from hallucination_detector import detect_hallucination
    from langgraph_agent import run_langgraph_agent
    import vector_store
    import db_config
    import schema_extractor
    
    app = FastAPI(title="Text-to-SQL API", version="1.0.0")
    
    # Allow React frontend to call this
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Load schema once at startup
    try:
        SCHEMA = get_schema()
    except Exception as e:
        print(f"Warning: Failed to initialize SCHEMA globally: {e}")
        SCHEMA = {}
    
    # Simple SQLite history store
    HISTORY_DB = Path(__file__).parent / "history.db"
    
    
    def init_history_db():
        conn = sqlite3.connect(HISTORY_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id TEXT PRIMARY KEY,
                question TEXT,
                sql TEXT,
                explanation TEXT,
                confidence REAL,
                row_count INTEGER,
                is_hallucination INTEGER,
                blocked INTEGER,
                block_reason TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    
    def save_to_history(record: dict):
        conn = sqlite3.connect(HISTORY_DB)
        conn.execute("""
            INSERT INTO query_history
            (id, question, sql, explanation, confidence, row_count,
             is_hallucination, blocked, block_reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["id"], record["question"], record.get("sql", ""),
            record.get("explanation", ""), record.get("confidence", 0),
            record.get("row_count", 0), int(record.get("is_hallucination", False)),
            int(record.get("blocked", False)), record.get("block_reason", ""),
            record["created_at"]
        ))
        conn.commit()
        conn.close()
    
    
    init_history_db()
    
    
    class QueryRequest(BaseModel):
        question: str
        previous_sql: Optional[str] = None
    
    
    @app.post("/v1/query_graph")
    async def query_db_graph(req: QueryRequest):
        """Deep Think Mode (LangGraph) Text-to-SQL pipeline."""
        try:
            query_id = str(uuid.uuid4())[:8]
            # Run the full agent graph
            result_payload = run_langgraph_agent(req.question, previous_sql=req.previous_sql)
    
            # Detect hallucinations on the final SQL if it exists
            hallucination_check = {"is_hallucination": False, "reason": ""}
            if result_payload["sql"]:
                hallucination_check = detect_hallucination(req.question, result_payload["sql"], 0.9, result_payload.get("result"))
                if hallucination_check["is_hallucination"]:
                    result_payload["explanation"] = "WARNING: Possible hallucination detected. " + hallucination_check["reason"] + "\n\n" + result_payload.get("explanation", "")
    
            # Log to DB
            record = {
                "id": query_id,
                "question": req.question,
                "sql": result_payload["sql"],
                "explanation": result_payload.get("explanation", ""),
                "confidence": 0.9,
                "row_count": len(result_payload.get("result", {}).get("rows", [])),
                "is_hallucination": hallucination_check["is_hallucination"],
                "blocked": False,
                "block_reason": "",
                "created_at": datetime.utcnow().isoformat()
            }
            save_to_history(record)
    
            return {
                "id": query_id,
                "status": "success",
                "sql": result_payload["sql"],
                "chart_config": result_payload.get("chart_config", {"type": "none"}),
                "result": result_payload.get("result", {})
            }
        
        except Exception as e:
            print(f"Error in /v1/query_graph: {str(e)}")
            return {"error": f"LangGraph Engine Error: {str(e)}"}
    
    
    @app.post("/v1/query")
    async def run_query(request: QueryRequest):
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
    
        query_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow().isoformat()
    
        # Step 1-3: Generate SQL, Check Guardrails, Execute with up to 2 retries
        max_retries = 2
        attempts = 0
        sql = ""
        explanation = ""
        llm_confidence = 0.5
        chart_config = None
        execution = None
        guardrail = {"passed": False, "reason": "Failed to start"}
    
        while attempts <= max_retries:
            try:
                if attempts == 0:
                    generation = generate_sql(question, SCHEMA, previous_sql=request.previous_sql)
                else:
                    generation = generate_sql(question, SCHEMA, previous_sql=sql, error_message=execution["error"])
            except Exception as e:
                if "API_KEY_INVALID" in str(e) or "400" in str(e):
                    return {"error": "Invalid Gemini API Key. Please check your backend/.env file."}
                return {"error": f"LLM Error: {str(e)}"}
    
            sql = generation.get("sql", "")
            explanation = generation.get("explanation", "")
            llm_confidence = generation.get("confidence", 0.5)
            chart_config = generation.get("chart_config", None)
    
            guardrail = validate_sql(sql, question)
            if not guardrail["passed"]:
                # If guardrails fail, we don't retry, we just block
                break
    
            execution = execute_sql_safely(sql)
            if execution["success"] or attempts == max_retries:
                break
            
            attempts += 1
    
        if not guardrail["passed"]:
            record = {
                "id": query_id, "question": question, "sql": sql,
                "blocked": True, "block_reason": guardrail["reason"],
                "created_at": created_at
            }
            save_to_history(record)
            return {
                "id": query_id,
                "question": question,
                "sql": sql,
                "blocked": True,
                "block_reason": guardrail["reason"],
                "result": None,
                "hallucination": None,
                "chart_config": chart_config,
                "created_at": created_at
            }
    
        # Step 4: Hallucination detection
        hallucination = detect_hallucination(
            original_question=question,
            sql=sql,
            llm_confidence=llm_confidence,
            execution_result=execution
        )
    
        # Step 5: Performance profiling
        performance_profile = profile_query(sql)
    
        # Step 6: Save history
        record = {
            "id": query_id,
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "confidence": hallucination["final_confidence"],
            "row_count": execution.get("row_count", 0),
            "is_hallucination": hallucination["is_hallucination"],
            "blocked": False,
            "block_reason": "",
            "created_at": created_at
        }
        save_to_history(record)
    
        return {
            "id": query_id,
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "blocked": False,
            "block_reason": None,
            "result": {
                "columns": execution["columns"],
                "rows": execution["rows"],
                "row_count": execution["row_count"],
                "error": execution["error"]
            },
            "hallucination": hallucination,
            "chart_config": chart_config,
            "performance_profile": performance_profile,
            "tables_used": generation.get("tables_used", []),
            "created_at": created_at
        }
    
    
    class ExecuteSqlRequest(BaseModel):
        sql: str
    
    @app.post("/v1/execute_sql")
    async def execute_custom_sql(req: ExecuteSqlRequest):
        sql = req.sql.strip()
        if not sql:
            raise HTTPException(status_code=400, detail="SQL cannot be empty")
        
        execution = execute_sql_safely(sql)
        return {
            "status": "success" if execution["success"] else "error",
            "result": {
                "columns": execution["columns"],
                "rows": execution["rows"],
                "row_count": execution["row_count"],
                "error": execution["error"]
            }
        }
    
    
    @app.get("/v1/schema")
    async def get_schema_endpoint():
        summary = []
        for table, info in SCHEMA.items():
            summary.append({
                "table": table,
                "columns": [c["name"] for c in info["columns"]],
                "row_count": info["row_count"],
                "foreign_keys": info["foreign_keys"]
            })
        return {"tables": summary, "total_tables": len(summary)}
    
    
    @app.get("/v1/history")
    async def get_history(limit: int = 20):
        conn = sqlite3.connect(HISTORY_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM query_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        conn.close()
    
        history = [dict(zip(cols, row)) for row in rows]
        return {"history": history, "count": len(history)}
    
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "tables": len(SCHEMA)}
    
    
    # --- Context Manager (RAG) Endpoints ---
    
    class ContextRequest(BaseModel):
        type: str = "sql"  # "sql" or "doc"
        question: Optional[str] = None
        sql: Optional[str] = None
        doc_text: Optional[str] = None
    
    
    @app.get("/v1/context")
    async def get_all_context():
        store = vector_store.load_store()
        # Don't send embeddings to frontend, they are large
        safe_store = []
        for r in store:
            safe_store.append({
                "id": r["id"],
                "type": r["type"],
                "question": r.get("question"),
                "sql": r.get("sql"),
                "doc_text": r.get("doc_text")
            })
        return {"context": safe_store}
    
    
    @app.post("/v1/context")
    async def add_context(req: ContextRequest):
        if req.type == "sql" and not (req.question and req.sql):
            raise HTTPException(status_code=400, detail="SQL training requires question and sql")
        if req.type == "doc" and not req.doc_text:
            raise HTTPException(status_code=400, detail="Doc training requires doc_text")
    
        try:
            new_id = vector_store.add_training_data(
                question=req.question,
                sql=req.sql,
                doc_text=req.doc_text,
                type=req.type
            )
            return {"status": "success", "id": new_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.delete("/v1/context/{record_id}")
    async def delete_context(record_id: str):
        vector_store.remove_training_data(record_id)
        return {"status": "success"}
    
    
    # --- Dynamic Database Endpoint ---
    
    class ConnectRequest(BaseModel):
        db_path: str
    
    
    @app.post("/v1/connect")
    async def connect_db(req: ConnectRequest):
        global SCHEMA
        try:
            db_config.set_db_path(req.db_path)
            # Regenerate schema for the new database
            try:
                new_schema = schema_extractor.get_schema()
                with open("schema.json", "w") as f:
                    json.dump(new_schema, f, indent=2)
                SCHEMA = new_schema
            except Exception as e:
                print(f"Warning: Failed to extract schema on update: {e}")
                SCHEMA = {}
            return {"status": "success", "db_path": req.db_path, "tables_found": len(SCHEMA)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/v1/connect")
    async def get_current_db():
        return {"db_path": db_config.get_db_path()}
    
    
    # --- Saved Dashboards Endpoints ---
    
    DASHBOARDS_FILE = "dashboards.json"
    
    def load_dashboards():
        if not Path(DASHBOARDS_FILE).exists():
            return []
        try:
            with open(DASHBOARDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    
    def save_dashboards(data):
        with open(DASHBOARDS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    class DashboardRequest(BaseModel):
        title: str
        question: str
        sql: str
        chart_config: dict
        data: list
    
    @app.get("/v1/dashboards")
    async def get_dashboards():
        return {"dashboards": load_dashboards()}
    
    @app.post("/v1/dashboards")
    async def save_dashboard(req: DashboardRequest):
        dashboards = load_dashboards()
        new_dash = {
            "id": str(uuid.uuid4())[:8],
            "title": req.title,
            "question": req.question,
            "sql": req.sql,
            "chart_config": req.chart_config,
            "data": req.data,
            "created_at": datetime.now().isoformat()
        }
        dashboards.append(new_dash)
        save_dashboards(dashboards)
        return {"status": "success", "id": new_dash["id"]}
    
    @app.delete("/v1/dashboards/{dash_id}")
    async def delete_dashboard(dash_id: str):
        dashboards = load_dashboards()
        dashboards = [d for d in dashboards if d["id"] != dash_id]
        save_dashboards(dashboards)
        return {"status": "success"}
    
    if __name__ == "__main__":
        import uvicorn
        import os
        port = int(os.getenv("PORT", 8080))
        uvicorn.run("main:app", host="0.0.0.0", port=port)
    
except Exception as e:
    error_trace = traceback.format_exc()
    print("FATAL BOOT ERROR:")
    print(error_trace)
    
    app = FastAPI(title="Error Server")
    
    @app.get("/")
    def read_error():
        return {"fatal_boot_error": error_trace}
        
    @app.get("/{path:path}")
    def read_error_all(path: str):
        return {"fatal_boot_error": error_trace}
        
    if __name__ == "__main__":
        port_str = os.getenv("PORT")
        port = int(port_str) if port_str else 8080
        uvicorn.run(app, host="0.0.0.0", port=port)
