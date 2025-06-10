import os
from llama_index import (
    SimpleDirectoryReader,
    GPTVectorStoreIndex,
    ServiceContext,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.openai import OpenAIEmbedding

INDEX_DIR = "storage"
INDEX_FILE = os.path.join(INDEX_DIR, "index.json")

# Carrega a API key do ambiente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

# Define embedding
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
