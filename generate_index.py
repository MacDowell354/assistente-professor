import os
from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_DIR = "storage"

# Configura o modelo de embedding do OpenAI
embedding_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

Settings.embed_model = embedding_model

def build_index():
    # Sempre cria a pasta de índice (caso não exista)
    os.makedirs(INDEX_DIR, exist_ok=True)

    # Carrega os dados da transcrição
    docs = SimpleDirectoryReader(input_files=["transcricoes.txt"]).load_data()

    # Cria o índice a partir dos documentos
    index = GPTVectorStoreIndex.from_documents(docs)

    # Salva o índice no disco
    index.save_to_disk(os.path.join(INDEX_DIR, "index.json"))

    print(f"✅ Índice gerado em '{INDEX_DIR}' com {len(docs)} documentos.")

if __name__ == "__main__":
    build_index()
