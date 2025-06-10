import openai
import os

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")
openai.api_key = api_key

def generate_answer(question: str, context: str = "", history: list = None) -> str:
    prompt = f"Contexto:\n{context}\n\nPergunta: {question}\nResposta:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']
