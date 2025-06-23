import os
from llama_index.core import (
    SimpleDirectoryReader,
    GPTVectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding

# Caminho para o diretório do índice
INDEX_DIR = "storage"
INDEX_FILE = os.path.join(INDEX_DIR, "index.json")

# Carrega a chave da OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

# Configura o modelo de embedding
embedding_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)
Settings.embed_model = embedding_model

# Função que cria ou carrega o índice
def load_or_build_index():
    if os.path.exists(INDEX_FILE):
        print("📁 Índice encontrado. Carregando...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        return load_index_from_storage(storage_context)
    else:
        print("🛠️ Índice não encontrado. Construindo novo...")
        docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        index = GPTVectorStoreIndex.from_documents(docs, storage_context=storage_context)
        index.storage_context.persist()
        return index

# Inicializa o índice
index = load_or_build_index()

# Função de busca de contexto
def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    response_str = str(response).strip().lower()

    # Bloqueios para evitar respostas inúteis
    if not response_str or response_str in ["", "none", "null"]:
        return ""

    frases_bloqueadas = ["não tenho certeza", "desculpe"]
    if any(f in response_str for f in frases_bloqueadas):
        return ""

    termos_proibidos = [
        "instagram", "vídeos para instagram", "celular para gravar",
        "smartphone", "tiktok", "post viral", "gravar vídeos",
        "microfone", "câmera", "edição de vídeo", "hashtags", "stories",
        "marketing de conteúdo", "produção de vídeo", "influencer"
    ]
    if any(termo in response_str for termo in termos_proibidos):
        return ""

    return response_str
