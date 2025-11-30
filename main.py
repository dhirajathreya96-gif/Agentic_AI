from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessageGraph, add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Assuming tools are available in tools.py
# If they are not actual LangChain tools, you might need to use a RunnablePassthrough
# For simplicity, we assume check_calendar_availability and schedule_new_meeting
# are callable objects that take a string and return a string.
# If they are not runnables, you may need to wrap them:
# from langchain_core.runnables import RunnableLambda
# check_calendar_availability = RunnableLambda(tools.check_calendar_availability)
# schedule_new_meeting = RunnableLambda(tools.schedule_new_meeting)

# Placeholder for tools if they are missing
class MockTool:
    def invoke(self, input):
        return f"Tool called with input: {input}"

try:
    from tools import check_calendar_availability, schedule_new_meeting
except ImportError:
    print("WARNING: Could not import tools. Using mock tools for testing.")
    check_calendar_availability = MockTool()
    schedule_new_meeting = MockTool()

# -----------------------------------------------------------------------------
# Agent State
# -----------------------------------------------------------------------------
class AgentState(dict):
    """Memory/state container for LangGraph."""
    # We must explicitly define 'messages' as the key for LangGraph state
    messages: list[BaseMessage]

load_dotenv()


# -----------------------------------------------------------------------------
# Build the ReAct Graph
# -----------------------------------------------------------------------------

# Router to check if the LLM output is a final answer or an action
def route_to_action_or_end(state: AgentState) -> str:
    """Determine whether to continue the loop by calling the action tool or end."""
    last = state["messages"][-1]
    
    # Check if the last message contains the ReAct Action signal
    if "Action:" in last.content:
        return "action"
    else:
        # If no action is found, this means the LLM has given its final answer
        # and we can transition to END.
        return END


def call_llm(state: AgentState):
    """Call the LLM and append its message."""
    # We remove the temperature=0 to allow the model to better follow ReAct prompting
    llm = ChatOpenAI(model="gpt-4o-mini")

    response = llm.invoke(state["messages"])
    # The LangGraph StateGraph handles appending the response for us if we return the state
    return {"messages": [response]}


def execute_action(state: AgentState):
    """Execute the tool called by the LLM."""
    last = state["messages"][-1]

    # Naive parse of ReAct format
    tool_name = None
    tool_input = None
    
    # This parsing is brittle; a more robust way is recommended for production.
    lines = last.content.split("\n")
    for line in lines:
        if line.startswith("Action:"):
            tool_name = line.replace("Action:", "").strip()
        if line.startswith("Action Input:"):
            tool_input = line.replace("Action Input:", "").strip()

    if not tool_name or not tool_input:
        # Handle case where LLM attempts an action but fails to format input
        result = "Error: Tool name or input could not be parsed."
    elif tool_name == "check_calendar_availability":
        result = check_calendar_availability.invoke(tool_input)
    elif tool_name == "schedule_new_meeting":
        result = schedule_new_meeting.invoke(tool_input)
    else:
        result = f"Unknown tool: {tool_name}"

    # Append the tool Observation as an AIMessage to the state
    return {"messages": [AIMessage(content=f"Observation: {result}")]}


# Create graph
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("action", execute_action)

graph.set_entry_point("llm")

# Conditional Edge: After LLM call, route to 'action' or 'END'
graph.add_conditional_edges(
    "llm",          # Source node
    route_to_action_or_end, # Router function
    {"action": "action", END: END} # Mapping of router output to target node
)

# After Action, always loop back to the LLM for the next thought/step
graph.add_edge("action", "llm")

react_agent = graph.compile()


# -----------------------------------------------------------------------------
# FastAPI Endpoint
# -----------------------------------------------------------------------------
app = FastAPI(title="ReAct Agent Backend")


class ChatRequest(BaseModel):
    session_id: str
    prompt: str


memory: Dict[str, AgentState] = {}


def get_state(session_id: str) -> AgentState:
    if session_id not in memory:
        # Initialize the state with an empty list of messages
        memory[session_id] = AgentState(messages=[])
    return memory[session_id]


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    state = get_state(req.session_id)
    
    # Append the new human message to the state
    state["messages"].append(HumanMessage(content=req.prompt))

    # Invoke the agent with the updated state
    # LangGraph returns the full, updated state upon completion
    output_state = react_agent.invoke(state)
    
    # The output_state is the final state after the graph completes.
    # Update the global memory state
    memory[req.session_id] = output_state

    # Extract the last message content for the FastAPI response
    final_msg = output_state["messages"][-1].content

    return {"response": final_msg}