import os
from llama_index import load_index_from_storage, ServiceContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms import OpenAI
from llama_index.storage.storage_context import StorageContext

embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

service_context = ServiceContext.from_defaults(embed_model=embed_model)

storage_context = StorageContext.from_defaults(persist_dir="storage")
index = load_index_from_storage(storage_context, service_context=service_context)

def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    return str(response)
