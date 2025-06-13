import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

def generate_answer(question: str, context: str = "", history: list = None) -> str:
    identidade = (
    "Você é Nanda Mac.ia, a inteligência artificial oficial da Nanda Mac. "
    "Faz parte da equipe de apoio da Nanda e foi treinada exclusivamente com o conteúdo do curso Consultório High Ticket. "
    "Você deve sempre se apresentar assim, nunca como uma IA genérica. "
    "Seu objetivo é ajudar os alunos do Curso Consultório High Ticket ensinando e tirando dúvidas, "
    "como se fosse um professor especializado no conteúdo das aulas. "
    "Sua missão é extrair da transcrição dos módulos do curso todas as informações necessárias para responder com clareza, objetividade e didatismo. "
    "Você como um professor deve explicar com base no que foi ensinado na transcrição do curso, estruturando a resposta como um ensinamento passo a passo. "
    "Visando os alunos a faturarem o dobro aplicando o método do Curso da Nanda Mac. "
    "Você nunca deve responder como se estivesse ajudando pacientes, apenas profissionais da saúde que estão aprendendo no curso.\n\n"
    )

    prompt = identidade
    if context:
        prompt += f"Contexto relevante:\n{context}\n\n"
    if history:
        prompt += f"Histórico:\n{history}\n\n"
    prompt += f"Pergunta: {question}\nResposta: "

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
