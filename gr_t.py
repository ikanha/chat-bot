from langgraph.func import entrypoint
from langgraph.store.memory import InMemoryStore
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()
store = InMemoryStore(
    index={
        'dims':1536,
        'embed': "openai:text-embedding-3-small"
    }
)

llm = init_chat_model('gpt-5.1')

from