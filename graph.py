from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from typing import TypedDict, Dict
from prompts import *

load_dotenv()

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment/secrets!")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key
    )

llm = get_llm()


class AgentState(TypedDict):
    user_prompt: str
    plan: str
    task_plan: str
    code_files: Dict[str, str]


def planner_agent(state: dict) -> dict:
    user_prompt = state["user_prompt"]

    resp = llm.invoke(planner_prompt(user_prompt))

    return {"plan": resp.content}


def architect_agent(state: dict) -> dict:
    plan = state["plan"]

    resp = llm.invoke(architect_prompt(plan))

    return {"task_plan": resp.content}




import re
import json

def safe_json_extract(text: str):
    # extract first JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found:\n{text}")

    return json.loads(match.group())

def coder_agent(state: dict) -> dict:
    task_plan = state["task_plan"]

    prompt = coder_prompt(task_plan)
    resp = llm.invoke(prompt)
    raw = resp.content

    try:
        files = safe_json_extract(raw)
    except Exception as e:
        raise ValueError(f"JSON parsing failed: {e}\n\nRAW:\n{raw}")

    if "files" not in files:
        raise ValueError(f"Missing 'files' key:\n{files}")

    return {"code_files": files["files"]}


graph = StateGraph(AgentState)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")

graph.set_entry_point("planner")

agent = graph.compile()


import os

def save_files(files: dict):
    base_dir = "generated_project"
    os.makedirs(base_dir, exist_ok=True)

    for path, content in files.items():   # files is Dict[str, str]
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
    print(result)
