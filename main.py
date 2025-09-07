import json
import asyncio
from typing import Annotated, Literal, TypedDict
from functools import partial

from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import messages_from_dict, messages_to_dict
from pydantic import BaseModel, Field

# MCP imports
from mcp_config import mcp_manager
from mcp_tools import MCP_TOOLS_CONFIG, determine_and_execute_tools

# --- 1. Agent and Model Configuration (EXPANDED) ---
LOCAL_MODEL_NAME = "llama3.2" # Kept as per your request

# EXPANDED: Added all the new agent personas with their system prompts
AGENT_CONFIG = {
    "therapist": {
        "prompt": """You are a compassionate therapist. Focus on the emotional aspects of the user's message.
                     Show empathy, validate their feelings, and help them process their emotions.
                     Avoid giving logical solutions unless explicitly asked."""
    },
    "logical": {
        "prompt": """You are a purely logical assistant. Focus only on facts and information.
                     Provide clear, concise answers based on logic and evidence.
                     Do not address emotions or provide emotional support."""
    },
    "planner": {
        "prompt": """You are a meticulous project manager. Your goal is to create clear, step-by-step plans.
                     Break down the user's request into a numbered or bulleted list of concrete actions."""
    },
    "coder": {
        "prompt": """You are an expert programmer and tech support agent. Provide clear, accurate code snippets.
                     When explaining, be precise and use technical terms correctly. Always format code in markdown code blocks."""
    },
    "brainstormer": {
        "prompt": """You are a highly creative idea-generation machine. Your goal is to provide a diverse and imaginative list of possibilities.
                     Don't worry about feasibility; focus on creativity. Use bullet points to list your ideas."""
    },
    "debater": {
        "prompt": """You are a skilled debater and critical thinker. Your purpose is to challenge the user's perspective and explore issues from all angles.
                     Present balanced arguments, clearly labeling the 'For' and 'Against' positions."""
    },
    "teacher": {
        "prompt": """You are a patient and skilled teacher. Your goal is to explain complex topics in a simple, intuitive way.
                     Use analogies, real-world examples, and avoid jargon where possible."""
    }
}

# MCP configuration is now handled in mcp_config.py
# Tool functions are now handled in mcp_tools.py

# --- 2. Pydantic Model for Structured Output (MODIFIED) ---
class MessageClassifier(BaseModel):
    # MODIFIED: Added all new types to the Literal list
    message_type: Literal[
        "therapist", "logical", "planner", "coder", "brainstormer", "debater", "teacher"
    ] = Field(
        ...,
        # MODIFIED: Updated description to give the LLM context for all choices
        description="Classify the user's message into one of the following categories: 'therapist', 'logical', 'planner', 'coder', 'brainstormer', 'debater', or 'teacher'."
    )

# --- 3. Graph State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str | None
    tool_results: dict | None  # Store MCP tool results
    available_tools: list | None  # Track which tools are available for current agent

# --- 4. Graph Nodes ---
def classify_message(state: State):
    llm = ChatOllama(model=LOCAL_MODEL_NAME, format="json")
    classifier_llm = llm.with_structured_output(MessageClassifier)
    last_message = state["messages"][-1]

    # MODIFIED: The classification prompt now includes instructions for all agent types
    classification_prompt = f"""Based on the user's message, classify their intent into one of the following categories:
- 'therapist': For messages about feelings, emotions, or personal problems.
- 'logical': For messages asking for facts, information, or objective analysis.
- 'planner': For messages asking 'how to', for a plan, or for steps to achieve a goal.
- 'coder': For messages containing code, error messages, programming help, or file operations (read, write, show, display, open files).
- 'brainstormer': For messages asking for creative ideas, names, or brainstorming help.
- 'debater': For messages that ask for pros and cons, arguments, or explore a controversial topic.
- 'teacher': For messages asking for a simple explanation of a complex topic.

IMPORTANT: If the message mentions specific files (like .py, .md, .txt, .json files) or asks to read/write/show/display/open files, classify as 'coder'.

User message: "{last_message.content}"
"""
    
    result = classifier_llm.invoke(classification_prompt)
    # The Pydantic model now forces the 'message_type' to be one of the agent names
    agent_name = result.message_type
    available_tools = MCP_TOOLS_CONFIG.get(agent_name, [])
    
    return {
        "next_agent": agent_name,
        "available_tools": available_tools,
        "tool_results": {}
    }

def agent_node(state: State, agent_name: str):
    config = AGENT_CONFIG[agent_name]
    llm = ChatOllama(model=LOCAL_MODEL_NAME)
    
    # Get available tools and execute them if needed
    available_tools = state.get("available_tools", [])
    user_message = state["messages"][-1].content
    
    # Execute tools using the new MCP system with proper filename extraction
    tool_results = {}
    if available_tools:
        # Use the advanced tool execution that handles filename extraction
        import asyncio
        try:
            tool_results = asyncio.run(determine_and_execute_tools(agent_name, user_message))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # Fallback: use threading for async execution
                import threading
                result = [{}]
                
                def run_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result[0] = loop.run_until_complete(determine_and_execute_tools(agent_name, user_message))
                    loop.close()
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join()
                tool_results = result[0]
    
    # Prepare system prompt with tool information
    system_prompt = config["prompt"]
    if tool_results:
        tool_info = "\n\nTool Results:\n"
        for tool, result in tool_results.items():
            # Truncate very long results for the prompt
            truncated_result = result[:1000] + "..." if len(result) > 1000 else result
            tool_info += f"- {tool}: {truncated_result}\n"
        system_prompt += tool_info
    
    messages = [
        {"role": "system", "content": system_prompt},
        state["messages"][-1]
    ]
    
    response_stream = llm.stream(messages)
    
    full_response = ""
    print("\nAssistant: ", end="", flush=True)
    for chunk in response_stream:
        print(chunk.content, end="", flush=True)
        full_response += chunk.content
    print("\n")

    return {
        "messages": [("assistant", full_response)],
        "tool_results": tool_results
    }

# --- 5. Graph Edge Logic (The Router) ---
def router(state: State):
    # The fallback to 'logical' is a safe default if classification is unclear
    agent_name = state.get("next_agent", "logical")
    return agent_name

# --- 6. Build the Graph (EXPANDED) ---
graph_builder = StateGraph(State)

# Add the single classifier node
graph_builder.add_node("classifier", classify_message)

# EXPANDED: Add a node for every agent in our config
for agent_name in AGENT_CONFIG:
    graph_builder.add_node(agent_name, partial(agent_node, agent_name=agent_name))

# The graph always starts at the classifier
graph_builder.add_edge(START, "classifier")

# EXPANDED: The conditional router now knows about all possible agents
graph_builder.add_conditional_edges(
    "classifier",
    router,
    # Creates a mapping from each agent name to its own node
    {agent_name: agent_name for agent_name in AGENT_CONFIG}
)

# EXPANDED: Add an end-point for every agent node
for agent_name in AGENT_CONFIG:
    graph_builder.add_edge(agent_name, END)

graph = graph_builder.compile()

# --- 7. Main Chatbot Loop (Unchanged) ---
HISTORY_FILE = "conversation_history.json"

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            list_of_dicts = json.load(f)
            return {"messages": messages_from_dict(list_of_dicts)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"messages": []}

def save_history(state):
    with open(HISTORY_FILE, "w") as f:
        serializable_messages = messages_to_dict(state["messages"])
        json.dump(serializable_messages, f, indent=2)

def run_chatbot():
    state = load_history()

    while True:
        user_input = input("You: ")
        if user_input.lower() == "q":
            save_history(state)
            print("Assistant: Goodbye!")
            break

        state["messages"].append(("user", user_input))
        result_state = graph.invoke(state)
        
        state = result_state

if __name__ == "__main__":
    # Initialize MCP clients
    asyncio.run(mcp_manager.initialize_servers())
    run_chatbot()