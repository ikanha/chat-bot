import os
import json
from dotenv import load_dotenv

from pymongo import MongoClient
from langgraph.store.mongodb import MongoDBStore
from langgraph.prebuilt import ToolNode, tools_condition
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.utils.config import get_config
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from typing import Optional

load_dotenv()


class UserProfile(BaseModel):
    user_name:      Optional[str] = None
    user_phone:     Optional[str] = None
    user_nick_name: Optional[str] = None


MONGO_URI = os.getenv("MONGO_URI")

client     = MongoClient(MONGO_URI)
collection = client["Telegram_bot"]["memories"]

store = MongoDBStore(collection=collection)

checkpointer = MemorySaver()


llm = init_chat_model("gpt-4o-mini")

memory_tools = [
    create_manage_memory_tool(
        namespace=("memories", "{user_name}"),
        schema=UserProfile,
    ),
    create_search_memory_tool(
        namespace=("memories", "{user_name}"),
    ),
]

llm_with_tools = llm.bind_tools(memory_tools)



class State(MessagesState):
    pass



def prompt(state: State):
    config    = get_config()
    user_name = config.get("configurable", {}).get("user_name", "default")

    try:
        memories = store.search(("memories", user_name))
    except Exception as e:
        print(f"Memory search error: {e}")
        memories = []

    if memories:
        # Include the memory ID so the LLM can pass it when updating
        memory_text = "\n".join(
            f"- id={m.key} | {json.dumps(m.value)}" for m in memories
        )
    else:
        memory_text = "No memories yet."

    system = SystemMessage(
        content=(
            "You are a helpful assistant.\n"
            "When the user shares personal info like their name, phone number, "
            "or nickname, ALWAYS save it using the manage_memory tool — "
            "fill in only the fields you know, leave others as null.\n"
            "Never save a memory where ALL fields are null.\n"
            "When UPDATING an existing memory, you MUST pass the exact memory id shown below.\n"
            "When creating a NEW memory (no existing entry), do NOT pass an id.\n\n"
            f"Existing memories:\n{memory_text}"
        )
    )
    return {"messages": [system] + state["messages"]}


def agent(state: State):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


builder = StateGraph(State)

builder.add_node("prompt", prompt)
builder.add_node("agent",  agent)
builder.add_node("tools",  ToolNode(tools=memory_tools))

builder.add_edge(START, "prompt")
builder.add_edge("prompt", "agent")
builder.add_conditional_edges("agent", tools_condition)  # → tools or END
builder.add_edge("tools", "agent")


graph = builder.compile(
    checkpointer=checkpointer,
    store=store,
)


# ── Chat Loop ──────────────────────────────────────────────────────────────────
config = {
    "configurable": {
        "thread_id": "thread-1",
        "user_name":  "kanhaiya",
    }
}

if __name__ == "__main__":
    try:
        while True:
            text = input("You: ")
            if text.lower() == "quit":
                break

            response = graph.invoke(
                {"messages": [HumanMessage(content=text)]},
                config=config,
            )
            print("Bot:", response["messages"][-1].content)

    finally:
        client.close()  # close MongoDB connection cleanly on exit
        print("MongoDB connection closed.")