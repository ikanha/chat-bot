import os
from dotenv import load_dotenv
from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import trim_messages
from langchain_core.messages import HumanMessage , AIMessage ,SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from utils.prompts import SYSTEM_MESSAGES
load_dotenv()

checkpoint = InMemorySaver()

user_list = ["7000983805"]

llm = ChatOpenAI(
    model="gpt-5-mini",
    streaming=True
)



class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    user_phone: str = Field(..., description="10 digit phone number")
    auth: bool | None = None


def start(state: AgentState):

    # if state.user_phone not in user_list:
    if False:
        print("User not authenticated")

        if state.messages and isinstance(state.messages[-1], AIMessage) and state.messages[-1].content == "User not authenticated":
            return {"auth": False}

        return {
            "auth": False,
            "messages": [AIMessage(content="User not authenticated")]
        }

    else:
        return {
            "auth": True,

        }


def auth_router(state: AgentState):
    if state.auth:
        return "chatbot"
    return END


def chatbot(state: AgentState):

    messages = SYSTEM_MESSAGES + state.messages
    response = llm.invoke(messages)
    return {
        "messages": [response]
    }


graph = StateGraph(AgentState)

graph.add_node("start", start)
graph.add_node("chatbot", chatbot)

graph.set_entry_point("start")

graph.add_conditional_edges(
    "start",
    auth_router
)

graph.add_edge("chatbot", END)

app = graph.compile(checkpointer=checkpoint)

if __name__ == "__main__":

    print("Opening test graph")

    phone = input("Enter phone number: ")

    while True:

        text = input("Enter your message: ")

        if text == "exit":
            break

        replay = app.invoke(
            {
                "messages": [HumanMessage(content=text)],
                "user_phone": phone
            },
            config={"configurable": {"thread_id": phone}}
        )

        if "messages" in replay:
            print("Replay:", replay["messages"][-1].content)
        else:
            print("Conversation ended (unauthorized user)")