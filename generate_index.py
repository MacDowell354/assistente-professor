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
    # Garante que a pasta de índice exista
    os.makedirs(INDEX_DIR, exist_ok=True)

    # Carrega os documentos da transcrição
    docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()

    # Cria o índice com persistência
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
    index = GPTVectorStoreIndex.from_documents(docs, storage_context=storage_context)

    # Salva no disco
    index.storage_context.persist()

    print(f"✅ Índice gerado em '{INDEX_DIR}' com {len(docs)} documentos.")

if __name__ == "__main__":
    build_index()
