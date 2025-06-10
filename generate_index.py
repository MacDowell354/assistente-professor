import os
from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_DIR = "storage"

embedding_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# Aplica o embedding globalmente
Settings.embed_model = embedding_model

def build_index():
    if not os.path.isdir(INDEX_DIR):
        os.makedirs(INDEX_DIR, exist_ok=True)
        docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()
        index = GPTVectorStoreIndex.from_documents(docs)
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        index.storage_context = storage_context
        index.save_to_disk(os.path.join(INDEX_DIR, "index.json"))
        print(f"✅ Índice gerado em '{INDEX_DIR}' com {len(docs)} documentos.")
    else:
        print(f"📁 Índice já existe em '{INDEX_DIR}', pulando geração.")

if __name__ == "__main__":
    build_index()
