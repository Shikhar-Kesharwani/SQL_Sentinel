import json
import os
from typing import TypedDict, List, Dict, Any, Literal, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

import vector_store
from schema_extractor import get_schema, schema_to_prompt_string
from guardrails import execute_sql_safely, validate_sql

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    question: str
    previous_sql: Optional[str]
    context: Optional[str]
    all_table_names: Optional[List[str]]
    relevant_tables: Optional[List[str]]
    schema_ddl: str
    sql: str
    chart_config: Dict[str, Any]
    explanation: str
    confidence: float
    tables_used: List[str]
    ambiguous: bool
    clarification_needed: str
    db_result: Dict[str, Any]
    error: str
    iterations: int

# --- 2. STRUCTURED OUTPUT MODELS ---
class FilterTablesOutput(BaseModel):
    relevant_tables: List[str] = Field(description="List of table names strictly relevant to answering the question.")

class ChartConfig(BaseModel):
    type: Literal["bar", "line", "pie", "none"] = Field(description="The type of chart to display.")
    x_key: str = Field(description="The exact column name for the x-axis or category label.")
    y_key: str = Field(description="The exact column name for the y-axis or numerical value.")

class GenerateSqlOutput(BaseModel):
    sql: str = Field(description="The executable SQL query.")
    explanation: str = Field(description="One-sentence plain English explanation of what the query does.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")
    tables_used: List[str] = Field(description="Tables used in the SQL.")
    ambiguous: bool = Field(description="True if question is too vague.")
    clarification_needed: str = Field(description="Clarifying question if ambiguous.")
    chart_config: ChartConfig = Field(description="Chart rendering configuration.")

_llm = None
def get_llm():
    global _llm
    if _llm is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=api_key)
    return _llm

def get_attr_or_key(obj: Any, key: str, default: Any = None) -> Any:
    """Safely extract value whether obj is a dict or Pydantic model."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

# --- 4. NODES ---

def node_setup(state: AgentState) -> AgentState:
    """Gets RAG context and all table names."""
    question = state["question"]
    relevant_contexts = vector_store.get_relevant_context(question, top_k=3)
    context_str = ""
    for ctx in relevant_contexts:
        if ctx.get("type") == "sql":
            context_str += f"Q: {ctx.get('question')}\nSQL: {ctx.get('sql')}\n\n"
        elif ctx.get("type") == "doc":
            context_str += f"Documentation: {ctx.get('doc_text')}\n\n"
            
    schema = get_schema()
    all_table_names = list(schema.keys())
    
    return {
        **state,
        "context": context_str.strip(),
        "all_table_names": all_table_names,
        "iterations": state.get("iterations", 0)
    }

def node_filter_tables(state: AgentState) -> AgentState:
    """Uses LLM to pick exactly which tables are needed."""
    all_tables = state.get("all_table_names", [])
    if not all_tables:
        return {**state, "relevant_tables": []}

    prompt = f"""You are a database router. Given the user's question, pick the tables that contain the relevant information.
    
Available Tables: {', '.join(all_tables)}
    
Question: {state['question']}"""
    
    llm = get_llm()
    try:
        structured_llm = llm.with_structured_output(FilterTablesOutput)
        result = structured_llm.invoke(prompt)
        res_tables = get_attr_or_key(result, "relevant_tables", [])
        if not isinstance(res_tables, list):
            res_tables = []
        valid_tables = [t for t in res_tables if t in all_tables]
    except Exception:
        valid_tables = all_tables

    if not valid_tables:
        valid_tables = all_tables
        
    return {**state, "relevant_tables": valid_tables}

def node_get_schema(state: AgentState) -> AgentState:
    """Extracts DDL only for the chosen tables."""
    schema = get_schema()
    relevant = state.get("relevant_tables") or list(schema.keys())
    schema_str = schema_to_prompt_string(schema, relevant)
    return {**state, "schema_ddl": schema_str}

def node_generate_sql(state: AgentState) -> AgentState:
    """Generates the SQL query and chart config."""
    prompt = f"""You are a SQL expert. Generate a SQL query.

DATABASE SCHEMA:
{state.get('schema_ddl', '')}

EXAMPLE QUERIES:
{state.get('context', '')}

RULES:
1. Only use SELECT statements.
2. Always use LIMIT (max 1000 rows) unless counting/aggregating.
3. Use proper JOINs based on foreign keys.

QUESTION: {state['question']}"""

    if state.get("previous_sql"):
        prompt += f"\n\nFor conversational context, here is the PREVIOUS SQL query the user ran:\n```sql\n{state['previous_sql']}\n```"

    if state.get("error"):
        prompt += f"\n\nPREVIOUS ATTEMPT FAILED:\nSQL: {state.get('sql', '')}\nError: {state.get('error', '')}\nFix the query."
        
    llm = get_llm()
    structured_llm = llm.with_structured_output(GenerateSqlOutput)
    result = structured_llm.invoke(prompt)
    
    chart_cfg = get_attr_or_key(result, "chart_config", {"type": "none", "x_key": "", "y_key": ""})
    if hasattr(chart_cfg, "model_dump"):
        chart_cfg = chart_cfg.model_dump()
    elif hasattr(chart_cfg, "dict"):
        chart_cfg = chart_cfg.dict()

    return {
        **state,
        "sql": get_attr_or_key(result, "sql", ""),
        "explanation": get_attr_or_key(result, "explanation", ""),
        "confidence": get_attr_or_key(result, "confidence", 0.9),
        "tables_used": get_attr_or_key(result, "tables_used", []),
        "ambiguous": get_attr_or_key(result, "ambiguous", False),
        "clarification_needed": get_attr_or_key(result, "clarification_needed", ""),
        "chart_config": chart_cfg if isinstance(chart_cfg, dict) else {"type": "none", "x_key": "", "y_key": ""}
    }

def node_execute(state: AgentState) -> AgentState:
    """Executes the SQL safely and runs guardrails first."""
    sql = state.get("sql", "")
    
    validation = validate_sql(sql, state["question"])
    if not validation.get("passed"):
        return {
            **state,
            "error": validation.get("reason", "Guardrail check failed"),
            "iterations": state.get("iterations", 0) + 1
        }
        
    try:
        res = execute_sql_safely(sql)
        if not res.get("success"):
            return {
                **state, 
                "error": res.get("error", "Unknown execution error"),
                "iterations": state.get("iterations", 0) + 1
            }
        else:
            return {
                **state,
                "db_result": res,
                "error": None
            }
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "iterations": state.get("iterations", 0) + 1
        }

# --- 5. EDGE LOGIC ---
def should_continue(state: AgentState) -> str:
    if not state.get("error"):
        return "end"
    if state.get("iterations", 0) >= 3:
        return "end"
    return "generate"

# --- 6. BUILD GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("setup", node_setup)
workflow.add_node("filter_tables", node_filter_tables)
workflow.add_node("get_schema", node_get_schema)
workflow.add_node("generate_sql", node_generate_sql)
workflow.add_node("execute", node_execute)

workflow.set_entry_point("setup")
workflow.add_edge("setup", "filter_tables")
workflow.add_edge("filter_tables", "get_schema")
workflow.add_edge("get_schema", "generate_sql")
workflow.add_edge("generate_sql", "execute")

workflow.add_conditional_edges(
    "execute",
    should_continue,
    {
        "end": END,
        "generate": "generate_sql"
    }
)

graph = workflow.compile()

def run_langgraph_agent(question: str, previous_sql: str = None) -> dict:
    """Helper function to run the graph and format the output like /v1/query"""
    initial_state = {"question": question, "previous_sql": previous_sql, "iterations": 0}
    final_state = graph.invoke(initial_state)
    
    return {
        "sql": final_state.get("sql", ""),
        "explanation": final_state.get("explanation", ""),
        "confidence": final_state.get("confidence", 0.0),
        "tables_used": final_state.get("tables_used", []),
        "ambiguous": final_state.get("ambiguous", False),
        "clarification_needed": final_state.get("clarification_needed", ""),
        "chart_config": final_state.get("chart_config", {"type": "none", "x_key": "", "y_key": ""}),
        "result": final_state.get("db_result", {"error": final_state.get("error", "Unknown error")}) if final_state.get("error") else final_state.get("db_result", {})
    }
