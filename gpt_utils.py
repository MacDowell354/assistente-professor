
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_answer(question: str, context: str = "", history: list = None) -> str:
    prompt = f"Contexto:\n{context}\n\nPergunta: {question}\nResposta:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']
