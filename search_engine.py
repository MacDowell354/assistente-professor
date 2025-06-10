
import os
from llama_index.core import load_index_from_storage
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.settings import Settings
from llama_index.storage.storage_context import StorageContext

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

storage_context = StorageContext.from_defaults(persist_dir="storage")
index = load_index_from_storage(storage_context)

def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    return str(response)
