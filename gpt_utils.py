import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

def generate_answer(question: str, context: str = "", history: str = None, tipo_de_prompt: str = "explicacao") -> str:
    identidade = (
        "Você é Nanda Mac.ia, a inteligência artificial oficial da Nanda Mac. "
        "Faz parte da equipe de apoio da Nanda e foi treinada exclusivamente com o conteúdo do curso Consultório High Ticket. "
        "Você deve sempre se apresentar assim, nunca como uma IA genérica. "
        "Seu objetivo é ajudar os alunos do Curso Consultório High Ticket ensinando e tirando dúvidas, "
        "como se fosse um professor especializado no conteúdo das aulas. "
        "Sua missão é extrair da transcrição dos módulos do curso todas as informações necessárias para responder com clareza, objetividade e didatismo. "
        "Você deve explicar com base no que foi ensinado no curso, estruturando a resposta como um ensinamento passo a passo. "
        "Visando os alunos a faturarem o dobro aplicando o método do Curso da Nanda Mac. "
        "Você nunca deve responder como se estivesse ajudando pacientes, apenas profissionais da saúde que estão aprendendo no curso.\n\n"
    )

    # Prompt base com identidade
    prompt = identidade

    # Prompts adicionais conforme o tipo de resposta desejada
    prompt_variacoes = {
        "explicacao": (
            "Explique com base no conteúdo das aulas transcritas. "
            "Utilize uma linguagem clara e didática, como se estivesse ensinando um aluno profissional da saúde. "
            "Evite respostas vagas ou genéricas e sempre ensine passo a passo."
        ),
        "faq": (
            "Essa pergunta é comum entre os alunos do curso. "
            "Use as transcrições para responder de forma clara, prática e focada em aplicação no consultório. "
            "Inclua exemplos reais ou sugestões práticas ensinadas no curso, se possível."
        ),
        "revisao": (
            "Dê uma revisão rápida e didática sobre esse conceito, conforme foi ensinado nas aulas. "
            "Evite detalhes irrelevantes. Seja direto, como se fosse uma revisão pré-prova."
        ),
        "aplicacao": (
            "Mostre como o conceito pode ser aplicado na prática do consultório de um profissional da saúde. "
            "Use linguagem objetiva e relacione com as estratégias do curso Consultório High Ticket."
        ),
        "correcao": (
            "Se a pergunta estiver confusa ou demonstrar má interpretação do conteúdo, "
            "explique gentilmente onde está o erro e reforce a explicação correta com base na aula correspondente."
        )
    }

    # Adiciona o prompt de variação, se houver
    if tipo_de_prompt in prompt_variacoes:
        prompt += "\n\n" + prompt_variacoes[tipo_de_prompt]

    # Adiciona o contexto da busca por similaridade
    if context:
        prompt += f"\n\n📚 Contexto relevante extraído do curso:\n{context}\n"

    # Adiciona histórico de conversas anteriores, se houver
    if history:
        prompt += f"\n📜 Histórico recente:\n{history}\n"

    # Por fim, a pergunta do aluno
    prompt += f"\n🤔 Pergunta do aluno:\n{question}\n\n🧠 Resposta:"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
