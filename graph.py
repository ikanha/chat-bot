import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# memory checkpoint
checkpoint = InMemorySaver()

# LLM with streaming
llm = ChatOpenAI(
    model="gpt-5-mini",
    streaming=True
)

# agent state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# node
def chatbot(state: AgentState):

    response = llm.invoke(state["messages"])

    return {
        "messages": [response]
    }


# build graph
graph = StateGraph(AgentState)

graph.add_node("chatbot", chatbot)

graph.set_entry_point("chatbot")

graph.add_edge("chatbot", END)

# compile graph
app = graph.compile(checkpointer=checkpoint)