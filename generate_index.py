import os
from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_DIR = "storage"

# Configura o modelo de embedding
embedding_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

Settings.embed_model = embedding_model

def build_index():
    # Garante que a pasta de índice existe
    os.makedirs(INDEX_DIR, exist_ok=True)

    # Lê os documentos de transcrição
    docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()

    # Cria contexto de armazenamento persistente
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)

    # Gera o índice
    index = GPTVectorStoreIndex.from_documents(docs, storage_context=storage_context)

    # Salva o índice no disco
    index.storage_context.persist()

    print(f"✅ Índice gerado em '{INDEX_DIR}' com {len(docs)} documentos.")

if __name__ == "__main__":
    build_index()
