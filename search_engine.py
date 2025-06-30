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

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=api_key,
)

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
        print(f"✅ Índice construído com {len(docs)} documentos.")
        return index

index = load_or_build_index()

def retrieve_relevant_context(
    question: str,
    top_k: int = 3,
    chunk_size: int = 512,
    min_length: int = 60,     # Mais flexível
    min_words: int = 10,      # Mais flexível
    proibidos=None,
) -> str:
    proibidos = proibidos or [
        "exercício", "exercícios", "prancha", "superman", "alongamento", "remada", "costas", "lombar",
        "trabalho físico", "fisioterapia", "treino", "musculação", "coluna", "ginástica", "flexão", "abdominal", "elevação pélvica"
    ]
    print("🔎 DEBUG — Pergunta para contexto:", question)
    engine = index.as_query_engine(
        similarity_top_k=top_k,
        chunk_size=chunk_size
    )
    response = engine.query(question)
    response_str = str(response).strip()
    lower = response_str.lower()
    print("🔎 DEBUG — Contexto bruto retornado:", response_str)
    if (
        not lower or lower in ("none", "null") or
        any(frase in lower for frase in ["não tenho certeza", "desculpe", "não sei"]) or
        any(tp in lower for tp in proibidos) or
        len(response_str) < min_length or
        len(response_str.split()) < min_words
    ):
        print("🔎 DEBUG — Contexto considerado INSUFICIENTE")
        return ""
    print("🔎 DEBUG — Contexto aprovado")
    return response_str
