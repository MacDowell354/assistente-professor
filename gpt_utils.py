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
        "explicacao": (
            "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
            "estrutura em tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula.<br><br>"
        ),
        "faq": (
            "<strong>Objetivo:</strong> Essa é uma dúvida comum. Responda de forma objetiva, com sugestões práticas ensinadas no curso."
        ),
        "revisao": (
            "<strong>Objetivo:</strong> Fazer uma revisão rápida e clara. Enfatize os pontos-chave ensinados."
        ),
        "aplicacao": (
            "<strong>Objetivo:</strong> Mostrar como o conceito é aplicado na prática. Foque em uso real no consultório, segundo o método."
        ),
        "correcao": (
            "<strong>Objetivo:</strong> Corrigir o aluno com gentileza, reforçando a explicação correta com base no curso."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Contexto:</strong> A captação de pacientes high ticket ensinada no curso <u>não usa redes sociais ou tráfego pago</u>. "
            "Explique o método com foco em <strong>posicionamento, experiência do paciente, senso estético e autoridade</strong>. "
            "Corrija visões erradas sobre uso de marketing digital."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica ensinado no curso. "
            "Apresente o Health Plan como ferramenta, seus benefícios e como aplicá-lo no consultório. "
            "Use uma estrutura passo a passo, com destaque para a importância da mentalidade high ticket."
        )
    }

    # Constrói o prompt com base na variação
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")

    if context:
        prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"

    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"

    prompt += f"<br><strong>🤔 Pergunta do aluno:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
