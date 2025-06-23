import os
from llama_index.core import (
    SimpleDirectoryReader,
    GPTVectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding

# Caminhos de armazenamento
INDEX_DIR = "storage"
INDEX_FILE = os.path.join(INDEX_DIR, "index.json")

# Configura a API Key da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

# Define o modelo de embedding
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=api_key,
)

# Carrega ou constrói o índice
def load_or_build_index():
    if os.path.exists(INDEX_FILE):
        print("📁 Índice encontrado. Carregando do disco...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        return load_index_from_storage(storage_context)
    else:
        print("⚙️ Índice não encontrado. Construindo novo...")
        docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()
        index = GPTVectorStoreIndex.from_documents(docs)
        index.storage_context.persist(persist_dir=INDEX_DIR)
        return index

# Inicializa o índice ao carregar o módulo
index = load_or_build_index()

# Função de busca com tratamento de contexto inválido
def retrieve_relevant_context(question: str, top_k: int = 3) -> str:
    engine = index.as_query_engine(similarity_top_k=top_k)
    response = engine.query(question)
    response_str = str(response).strip().lower()

    # Bloqueios de respostas vazias ou não úteis
    if not response_str or response_str in ["", "none", "null"]:
        return ""

    frases_bloqueadas = ["não tenho certeza", "desculpe"]
    if any(frase in response_str for frase in frases_bloqueadas):
        return ""

    termos_proibidos = [
        "instagram", "vídeos para instagram", "celular para gravar", "smartphone",
        "tiktok", "post viral", "gravar vídeos", "microfone", "câmera",
        "edição de vídeo", "hashtags", "stories", "marketing de conteúdo",
        "produção de vídeo", "influencer"
    ]
    if any(termo in response_str for termo in termos_proibidos):
        return ""

    return response_str
