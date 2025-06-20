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
            "estruturada em tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula.<br><br>"
        ),
        "faq": (
            "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
            "Use explicações práticas, baseadas nos ensinamentos da Nanda Mac. "
            "Se possível, traga exemplos do consultório, sem usar marketing digital, e aplique o método passo a passo. "
            "Seja clara e ajude o aluno a enxergar como isso se aplica à rotina real."
        ),
        "revisao": (
            "<strong>Objetivo:</strong> Fazer uma revisão rápida e eficiente. "
            "Enfatize os pontos centrais ensinados no curso com clareza. "
            "Evite aprofundamento excessivo — pense como uma revisão antes da aplicação prática. "
            "Organize em tópicos curtos ou bullets quando possível."
        ),
        "aplicacao": (
            "<strong>Objetivo:</strong> Ensinar como aplicar o conceito no dia a dia do consultório. "
            "Use exemplos realistas e mostre o passo a passo como se estivesse ajudando o aluno a executar a técnica. "
            "Sempre use o método da Nanda Mac como referência principal. "
            "Evite termos técnicos demais. Foque em ações práticas e concretas."
        ),
        "correcao": (
            "<strong>Objetivo:</strong> Corrigir gentilmente qualquer erro ou confusão na pergunta do aluno. "
            "Mantenha o tom acolhedor, elogie o esforço do aluno e explique o conceito correto com base no curso. "
            "Reforce a explicação com um exemplo direto e didático. Nunca deixe o aluno constrangido."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Contexto:</strong> O método da Nanda Mac <u>não depende de redes sociais ou tráfego pago</u>. "
            "Explique como o aluno pode atrair pacientes de alto valor usando <strong>posicionamento, experiência do paciente, senso estético e autoridade offline</strong>. "
            "Corrija visões equivocadas que envolvam anúncios, parcerias digitais ou Instagram. "
            "Mostre como profissionais faturam alto apenas com posicionamento estratégico e experiência memorável no consultório."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica ensinado no curso. "
            "Apresente o Health Plan como ferramenta, seus benefícios e como aplicá-lo no consultório. "
            "Use uma estrutura passo a passo, com destaque para a importância da mentalidade high ticket."
        ),
        "health_plan": (
            "<strong>Objetivo:</strong> Ensinar o aluno a montar o Health Plan com a estrutura exata da Nanda Mac:<br><br>"
            "<strong>➡ Situação Atual:</strong> Ajude o aluno a descrever claramente o que o paciente está vivenciando no momento.<br>"
            "<strong>➡ Objetivo:</strong> Explique o que se espera alcançar com o tratamento. Seja direto e específico.<br>"
            "<strong>➡ Plano de Tratamento:</strong> Mostre quais passos e recursos o aluno vai aplicar no consultório.<br>"
            "<strong>➡ Previsibilidade de Retorno:</strong> Oriente como agendar o retorno, reforçando segurança e continuidade.<br>"
            "<strong>➡ Investimento:</strong> Mostre como apresentar o valor com confiança e clareza.<br><br>"
            "Sempre use exemplos realistas e linguagem direta, como a Nanda ensina. Nunca use termos genéricos ou acadêmicos."
        )
    }

    # 🚫 Fora do escopo se não houver contexto
    if not context or context.strip() == "":
        return (
            "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
            "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
            "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
            "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
        )

    # 🔧 Constrói o prompt completo
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")

    if context:
        prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"

    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"

    prompt += f"<br><strong>🤔 Pergunta do aluno:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 🏥 Se for health plan e a pergunta mencionar cirurgia, adiciona modelo de investimento cirúrgico
    termos_cirurgia = ["cirurgia", "cirúrgico", "hospital", "anestesia", "plástica", "equipe médica"]
    if tipo_de_prompt == "health_plan" and any(t in question.lower() for t in termos_cirurgia):
        prompt += (
            "<br><br><strong>💰 Investimento (modelo para cirurgias):</strong><br>"
            "O valor total do tratamento cirúrgico, considerando todos os envolvidos — equipe médica, anestesia e hospital — pode chegar até R$ X.XXX,00.<br><br>"
            "Esse valor já considera uma margem de segurança, pois alguns custos, como os valores cobrados pelo hospital ou pela equipe de anestesia, podem sofrer variações que não estão sob o meu controle.<br><br>"
            "Mas pode ficar tranquila: esse é o teto máximo que você pagaria, e ele já contempla todas as etapas necessárias para a realização do seu procedimento com segurança e qualidade.<br><br>"
            "Caso haja alguma redução nesses custos, você será informada — mas jamais ultrapassaremos esse valor combinado.<br><br>"
            "O mais importante aqui é que você esteja segura para seguir com tranquilidade e clareza em todo o processo.<br>"
        )

    # 🔁 Seleciona o modelo ideal
    if tipo_de_prompt in ["health_plan", "aplicacao", "precificacao", "capitacao_sem_marketing_digital"]:
        modelo_escolhido = "gpt-4"
    else:
        modelo_escolhido = "gpt-3.5-turbo"

    response = client.chat.completions.create(
        model=modelo_escolhido,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
