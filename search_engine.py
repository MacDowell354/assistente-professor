import os
from llama_index.core import (
    SimpleDirectoryReader,
    GPTVectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding

# Diretório onde o índice será salvo
INDEX_DIR = "storage"
INDEX_FILE = os.path.join(INDEX_DIR, "index.json")

# Carrega a chave da OpenAI da variável de ambiente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

# Configura o modelo de embedding da OpenAI
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=api_key,
)
Settings.embed_model = embed_model

# Função que cria ou carrega o índice
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

# Inicializa o índice ao importar este módulo
index = load_or_build_index()

# Função para buscar o contexto mais relevante com base em uma pergunta
def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    response_str = str(response).strip().lower()

    # Bloqueia respostas vazias ou irrelevantes
    if not response_str or response_str in ["", "none", "null"]:
        return ""

    # Bloqueia frases genéricas
    frases_bloqueadas = ["não tenho certeza", "desculpe"]
    if any(f in response_str for f in frases_bloqueadas):
        return ""

    # Bloqueia termos fora do escopo do curso
    termos_proibidos = [
        "instagram", "vídeos para instagram", "celular para gravar",
        "smartphone", "tiktok", "post viral", "gravar vídeos",
        "microfone", "câmera", "edição de vídeo", "hashtags", "stories",
        "marketing de conteúdo", "produção de vídeo", "influencer"
    ]
    if any(termo in response_str for termo in termos_proibidos):
        return ""

    return response_str
