import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

def generate_answer(question: str, context: str = "", history: str = None, tipo_de_prompt: str = "explicacao") -> str:
    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a inteligência artificial oficial da Nanda Mac. "
        "Faz parte da equipe de apoio da Nanda e foi treinada exclusivamente com o conteúdo do curso <strong>Consultório High Ticket</strong>. "
        "Seu papel é ensinar, orientar e responder às dúvidas dos alunos com clareza, objetividade e didatismo. "
        "Responda como se fosse uma professora experiente, ajudando o aluno a aplicar o método na prática. "
        "Nunca responda como se estivesse ajudando pacientes — apenas profissionais da saúde que estão aprendendo o conteúdo do curso.<br><br>"
    )

    prompt_variacoes = {
        "explicacao": "...",
        "faq": "...",
        "revisao": "...",
        "aplicacao": "...",
        "correcao": "...",
        "capitacao_sem_marketing_digital": "...",
        "precificacao": "...",
        "health_plan": "..."
    }

    # 🚫 Fora do escopo se não houver contexto
    if not context or context.strip() == "":
        return (
            "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
            "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
            "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
            "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
        )

    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")

    if context:
        prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"

    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"

    prompt += f"<br><strong>🤔 Pergunta do aluno:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 🔁 Define modelo baseado no tipo de prompt
    if tipo_de_prompt in ["health_plan", "aplicacao", "precificacao", "capitacao_sem_marketing_digital"]:
        modelo_escolhido = "gpt-4"
    else:
        modelo_escolhido = "gpt-3.5-turbo"

    response = client.chat.completions.create(
        model=modelo_escolhido,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
