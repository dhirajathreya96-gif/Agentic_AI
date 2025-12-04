import os
import uuid
import json
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage

from fastapi import FastAPI

from fastapi import FastAPI

app = FastAPI(title="Calendar ReAct Agent")

@app.get("/")
def root():
    return {"status": "Backend is running", "message": "Calendar AI API backend is live!"}



# Import ONLY the tool functions — NOT the Pydantic models
from tools import check_calendar_availability, schedule_new_meeting, tools

load_dotenv()

# -----------------------------
# Local Pydantic Versions
# (Safe: No dependency on auth)
# -----------------------------
from pydantic import BaseModel

class CheckAvailabilityInput(BaseModel):
    date: str
    time: str
    duration_minutes: int

class ScheduleMeetingInput(BaseModel):
    date: str
    time: str
    duration_minutes: int
    attendees: List[str]
    subject: str


# -----------------------------
# Tool Description Helper
# -----------------------------
def get_tool_info(tool):
    name = getattr(tool, "__name__", "unknown_tool")
    desc = getattr(tool, "__doc__", "No description available.")
    return f"{name}: {desc}"


# -----------------------------
# State
# -----------------------------
class AgentState(dict):
    messages: List[BaseMessage]
    loop_count: Optional[int]


# -----------------------------
# Prompts
# -----------------------------
tool_descriptions = "\n".join([get_tool_info(t) for t in tools])

SYSTEM_PROMPT = f"""
You are a helpful calendar assistant using two tools:

{tool_descriptions}

Follow ReAct format.

1. Thought:
2. Action: tool_name
3. Action Input: {{"json"}}
4. Final Answer:

Only call tools when needed.
"""


model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
MAX_STEPS = 5


# -----------------------------
# LLM Node
# -----------------------------
def call_llm(state: AgentState):
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    ai = model.invoke(msgs)
    state["loop_count"] = state.get("loop_count", 0) + 1
    return {"messages": [ai]}


# -----------------------------
# Execute Action
# -----------------------------
def execute_action(state: AgentState):
    last = state["messages"][-1]

    lines = last.content.split("\n")
    tool_name = None
    tool_input_raw = None

    for line in lines:
        line = line.strip()
        if line.startswith("Action:"):
            tool_name = line.replace("Action:", "").strip()
        elif line.startswith("Action Input:"):
            tool_input_raw = line.replace("Action Input:", "").strip().strip("`")

    if not tool_name or not tool_input_raw:
        return {"messages": [AIMessage(content="Observation: Invalid tool format.")]}

    # Parse JSON
    try:
        tool_input_data = json.loads(tool_input_raw)
    except:
        return {"messages": [AIMessage(content=f"Observation: Invalid JSON: {tool_input_raw}")]}

    # Validation + execution
    try:
        if tool_name == "check_calendar_availability":
            tool_input = CheckAvailabilityInput(**tool_input_data)
            result = check_calendar_availability(tool_input)

        elif tool_name == "schedule_new_meeting":
            tool_input = ScheduleMeetingInput(**tool_input_data)
            result = schedule_new_meeting(tool_input)

        else:
            result = f"Unknown tool: {tool_name}"

    except Exception as e:
        result = f"Tool Error: {e}"

    return {"messages": [AIMessage(content=f"Observation: {result}")]}


# -----------------------------
# Router
# -----------------------------
def route_to_action_or_end(state: AgentState):
    last = state["messages"][-1].content
    count = state.get("loop_count", 0)

    if count >= MAX_STEPS:
        state["messages"].append(AIMessage(content="Final Answer: Too many steps."))
        return END

    if "Final Answer:" in last:
        return END

    if "Action:" in last and "Action Input:" in last:
        return "action"

    state["messages"].append(AIMessage(content="Final Answer: Ambiguous response."))
    return END


# -----------------------------
# Graph
# -----------------------------
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("action", execute_action)

graph.set_entry_point("llm")
graph.add_conditional_edges("llm", route_to_action_or_end, {"action": "action", END: END})
graph.add_edge("action", "llm")

react_agent = graph.compile()


# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI(title="Calendar ReAct Agent")

class ChatRequest(BaseModel):
    session_id: str
    prompt: str

memory: Dict[str, AgentState] = {}


def get_state(session_id: str) -> AgentState:
    if session_id not in memory:
        memory[session_id] = AgentState(messages=[], loop_count=0)
    memory[session_id]["loop_count"] = 0
    return memory[session_id]


@app.post("/chat")
def chat(req: ChatRequest):
    state = get_state(req.session_id)
    state["messages"].append(HumanMessage(content=req.prompt))

    try:
        out = react_agent.invoke(state)
        memory[req.session_id] = out

        msg = out["messages"][-1].content
        if msg.startswith("Final Answer:"):
            msg = msg.replace("Final Answer:", "").strip()

        return {"response": msg}
    except Exception as e:
        return {"response": f"Error: {e}"}
