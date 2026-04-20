def planner_prompt(user_prompt: str) -> str:
    return f"""You are the PLANNER agent. Convert the user prompt into a COMPLETE engineering project plan.

User Request: {user_prompt}

Provide a structured plan with:
1. Project Goal
2. Key Features (list each clearly)
3. Suggested Tech Stack
4. High-level file/folder structure

Be specific and detailed.
"""


def architect_prompt(plan: str) -> str:
    return f"""You are the ARCHITECT agent. Given this project plan, break it down into explicit engineering tasks.

RULES:
- For each FILE in the plan, create one or more IMPLEMENTATION TASKS.
- In each task description:
  * Specify exactly what to implement.
  * Name the variables, functions, classes, and components to be defined.
  * Include integration details: imports, expected function signatures, data flow.
- Order tasks so that dependencies are implemented first.
- Each step must be SELF-CONTAINED but also carry FORWARD the relevant context from the plan.

Project Plan:
{plan}
"""


def coder_prompt(task_plan: str) -> str:
    return f"""You are a code generator. Your job is to generate complete, working source code files.

CRITICAL RULES:
- Output ONLY valid JSON — nothing else.
- NO markdown, NO explanation, NO code fences, NO text outside the JSON.
- The output MUST be parseable by json.loads().
- Escape all newlines inside strings as \\n.
- Use double quotes only (no single quotes in JSON keys or values).
- Generate COMPLETE file contents — do not truncate or use placeholders.

STRICT OUTPUT FORMAT:
{{
  "files": {{
    "filename.ext": "full file content here with \\n for newlines",
    "folder/another_file.ext": "full file content here"
  }}
}}

Task Plan:
{task_plan}
"""
