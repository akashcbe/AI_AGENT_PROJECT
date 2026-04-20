from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict
from prompts import planner_prompt, architect_prompt, coder_prompt
import re
import json

load_dotenv()

# --- Resolve API key ONCE at module load time ---
def _resolve_api_key() -> str:
    # 1. Try Streamlit secrets
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY", None)
        if key:
            return key
    except Exception:
        pass

    # 2. Try environment variable
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key

    return ""

GROQ_API_KEY = _resolve_api_key()


def get_llm():
    key = GROQ_API_KEY or _resolve_api_key()
    if not key:
        raise ValueError(
            "GROQ_API_KEY not found!\n"
            "• Streamlit Cloud: App Settings → Secrets → add GROQ_API_KEY\n"
            "• Local: add GROQ_API_KEY=your_key in a .env file"
        )
    return ChatGroq(model="llama-3.3-70b-versatile", api_key=key)


class AgentState(TypedDict):
    user_prompt: str
    plan: str
    task_plan: str
    code_files: Dict[str, str]


def planner_agent(state: dict) -> dict:
    llm = get_llm()
    resp = llm.invoke(planner_prompt(state["user_prompt"]))
    return {"plan": resp.content}


def architect_agent(state: dict) -> dict:
    llm = get_llm()
    resp = llm.invoke(architect_prompt(state["plan"]))
    return {"task_plan": resp.content}


def safe_json_extract(text: str):
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response:\n{text[:500]}")
    return json.loads(match.group())


def coder_agent(state: dict) -> dict:
    llm = get_llm()
    resp = llm.invoke(coder_prompt(state["task_plan"]))
    raw = resp.content
    try:
        files = safe_json_extract(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing failed: {e}\n\nRaw output:\n{raw[:800]}")
    if "files" not in files:
        raise ValueError(f"Missing 'files' key. Got: {list(files.keys())}")
    return {"code_files": files["files"]}


graph = StateGraph(AgentState)
graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)
graph.set_entry_point("planner")
graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_edge("coder", END)
agent = graph.compile()


def save_files(files: dict):
    base_dir = "generated_project"
    os.makedirs(base_dir, exist_ok=True)
    for path, content in files.items():
        full_path = os.path.join(base_dir, path)
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
