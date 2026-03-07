import os
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI",)

def get_mongo_checkpointe():
    client = MongoClient(MONGO_URI)
    db = client["Telegram_bot"]
    collection = db["conversations"]
    checkpointer = MongoDBSaver(collection)

    return checkpointer

