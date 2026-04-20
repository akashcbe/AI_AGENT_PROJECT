def planner_prompt(user_prompt:str) ->str:
    PLANNER_PROMPT = f"""
you are the PLANNER agent. convert the user prompt into a COMPLETE engineering project plan

user request:{user_prompt}
    
"""
    return PLANNER_PROMPT


def architect_prompt(plan:str)->str:
    ARCHITECT_PROMPT =f"""
        you are the ARCHITECT agent. Given this project plan, break it down into explicit engeering tasks.
        
        RULES:
        -For each FILE in the plan, create one or more IMPLEMENTATION TASK.
    -In each task description:
      * specify exactly what to implement.
      * Name the variables,functions,classes and components to be defined.
      * Include intergration details: imports, expected function signature, data flow
    -Order tasks so that dependencies andimplemented first.
    -Each step must be SELF-CONTANIED but also carry    FARWARD the relevant context from plan
    
    Project  Plan:
    {plan}
    """
    return ARCHITECT_PROMPT

def coder_prompt(task_plan: str) -> str:
    return f"""
You are a code generator.

CRITICAL RULES:
- Output ONLY valid JSON
- NO markdown
- NO explanation
- NO code fences
- NO text outside JSON
- MUST be parseable by json.loads()

STRICT FORMAT:
{{
  "files": {{
    "filename.ext": "file content as plain string"
  }}
}}

IMPORTANT:
- Escape newlines as \\n inside strings
- Use double quotes only

TASK PLAN:
{task_plan}
"""