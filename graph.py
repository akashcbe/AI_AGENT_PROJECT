from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict
from prompts import planner_prompt, architect_prompt, coder_prompt
import re
import json

load_dotenv()


def get_llm():
    # Try Streamlit secrets first (for cloud deployment), then env var
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("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")
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found! "
            "Set it in .streamlit/secrets.toml (for Streamlit Cloud) "
            "or as an environment variable."
        )

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key
    )


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
    """Robustly extract JSON from LLM output, stripping markdown fences if present."""
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
        raise ValueError(f"JSON parsing failed: {e}\n\nRaw output snippet:\n{raw[:800]}")

    if "files" not in files:
        raise ValueError(
            f"LLM response missing 'files' key. Got keys: {list(files.keys())}"
        )

    return {"code_files": files["files"]}


# --- Build LangGraph ---
graph = StateGraph(AgentState)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.set_entry_point("planner")
graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_edge("coder", END)

agent = graph.compile()


# --- Save Files to Disk ---
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


if __name__ == "__main__":
    result = agent.invoke({
        "user_prompt": "create a simple calculator web application"
    })
    save_files(result["code_files"])
    print("Files generated:", list(result["code_files"].keys()))
