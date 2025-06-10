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
    api_key=api_key,
)
service_context = ServiceContext.from_defaults(embed_model=embed_model)

# Lógica para carregar ou gerar o índice
def load_or_build_index():
    if os.path.exists(INDEX_FILE):
        print("📁 Índice encontrado. Carregando...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        return load_index_from_storage(storage_context, service_context=service_context)
    else:
        print("🛠️ Índice não encontrado. Construindo novo...")
        docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()
        index = GPTVectorStoreIndex.from_documents(docs, service_context=service_context)
        index.storage_context.persist(persist_dir=INDEX_DIR)
        return index

# Inicializa o índice
index = load_or_build_index()

# Função pública para responder perguntas
def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    return str(response)
