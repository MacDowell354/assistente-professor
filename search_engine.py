import os
from llama_index.core import (
    SimpleDirectoryReader,
    GPTVectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding

INDEX_DIR = "storage"
INDEX_FILE = os.path.join(INDEX_DIR, "index.json")

# Carrega a API key do ambiente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

# Define o embedding model
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=api_key,
)
Settings.embed_model = embed_model

# Carrega ou cria o índice
def load_or_build_index():
    if os.path.exists(INDEX_FILE):
        print("📁 Índice encontrado. Carregando...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        return load_index_from_storage(storage_context)
    else:
        print("🛠️ Índice não encontrado. Construindo novo...")
        docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()
        index = GPTVectorStoreIndex.from_documents(docs)
        index.storage_context.persist(persist_dir=INDEX_DIR)
        return index

# Inicializa o índice
index = load_or_build_index()

# Função para buscar contexto relevante da pergunta
def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    response_str = str(response).strip().lower()

    # ✅ Verifica vazio ou nulo
    if not response_str or response_str in ["", "none", "null"]:
        return ""

    # 🚫 Bloqueia conteúdos genéricos ou fora do escopo do curso
    termos_proibidos = [
        "instagram", "vídeos para instagram", "celular para gravar",
        "smartphone", "tiktok", "post viral", "gravar vídeos",
        "microfone", "câmera", "edição de vídeo", "hashtags", "stories",
        "marketing de conteúdo", "produção de vídeo", "influencer"
    ]

    for termo in termos_proibidos:
        if termo in response_str:
            return ""

    # Também bloqueia frases genéricas
    if "não tenho certeza" in response_str or "desculpe" in response_str:
        return ""

    return str(response)
