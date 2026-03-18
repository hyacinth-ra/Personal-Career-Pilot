import operator
from typing import Annotated, TypedDict, List, Union
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode


class AgentState(TypedDict):
    # 'messages' will store the entire history. 
    messages: Annotated[List[BaseMessage], operator.add]

# Define the Nodes
def call_model(state: AgentState, llm_with_tools):
    """Calls the LLM to decide the next action."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Define the Router
def router(state: AgentState):
    """Determines if we should use a tool or finish."""
    last_message = state["messages"][-1]
    
    # If the LLM didn't call any tools, we are done
    if not last_message.tool_calls:
        return END
    
    # Check if the last tool result was "No jobs found" 
    # This prevents saving empty files!
    for m in reversed(state["messages"]):
        if isinstance(m, ToolMessage) and "No high-quality jobs found" in m.content:
            print("🔄 Agent detected empty results. Retrying with better query...")
            return "agent" # Loop back to the agent to try a different query
            
    return "tools"

# Building the Graph
def create_job_research_graph(llm_with_tools, tools):
    workflow = StateGraph(AgentState)

    # Add our nodes
    workflow.add_node("agent", lambda state: call_model(state, llm_with_tools))
    workflow.add_node("tools", ToolNode(tools))

    # Set the Entry Point
    workflow.add_edge(START, "agent")

    # Add Conditional Logic
    workflow.add_conditional_edges(
        "agent",
        router,
        {
            "tools": "tools",
            "agent": "agent", # Loop for retry
            END: END
        }
    )

    # After tools run, always go back to agent to see the results
    workflow.add_edge("tools", "agent")

    return workflow.compile()