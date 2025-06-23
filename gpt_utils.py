import os
from openai import OpenAI, OpenAIError

# Obtém a chave de API\api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

# Mensagem padrão para perguntas fora de escopo
OUT_OF_SCOPE_MSG = (
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
    "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = "explicacao"
) -> str:
    # 🔍 Detecta perguntas sobre mensagens automáticas
    termos_mensagem_auto = [
        "mensagem automática", "whatsapp", "resposta automática",
        "fim de semana", "fora do horário", "responder depois", "robô"
    ]
    if any(t in question.lower() for t in termos_mensagem_auto):
        return (
            "Olá, querida! Vamos esclarecer isso com base no que a própria Nanda orienta no curso:<br><br>"
            "📌 A Nanda não recomenda o uso de <strong>mensagens automáticas genéricas</strong> no WhatsApp, "
            "especialmente aquelas como “já te respondo em breve” ou “assim que possível retorno”. "
            "Isso porque <strong>paciente High Ticket não gosta de respostas padrões ou que soem como robôs</strong>.<br><br>"
            "✨ O importante é responder com atenção, em horários específicos do dia. "
            "Psicólogas, por exemplo, geralmente não têm secretária — e está tudo bem. "
            "Os pacientes já entendem que você está em atendimento durante o dia.<br><br>"
            "💡 Se ainda assim quiser configurar algo, recomendo criar uma <strong>mensagem mais humana e acolhedora</strong>, "
            "que transmita segurança e cuidado, sem parecer fria ou automática.<br><br>"
            "Se quiser, posso te ajudar a montar uma mensagem assim agora mesmo. Deseja isso?"
        )

    # ✋ Se não há contexto relevante retornado da base de transcrições, fora de escopo
    if not context or not context.strip():
        return OUT_OF_SCOPE_MSG

    # Identidade do assistente
    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a inteligência artificial oficial da Nanda Mac. "
        "Faz parte da equipe de apoio da Nanda e foi treinada exclusivamente com o conteúdo do curso <strong>Consultório High Ticket</strong>. "
        "Seu papel é ensinar, orientar e responder às dúvidas dos alunos com clareza, objetividade e didatismo. "
        "Responda como se fosse uma professora experiente, ajudando o aluno a aplicar o método na prática. "
        "Nunca responda como se estivesse ajudando pacientes — apenas profissionais da saúde que estão aprendendo o conteúdo do curso.<br><br>"
    )

    # Templates de variações de prompt
    prompt_variacoes = {
        "explicacao": (
            "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
            "estruturada em tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula.<br><br>"
        ),
        "faq": (
            "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
            "Use explicações práticas, baseadas nos ensinamentos da Nanda Mac. "
            "Se possível, traga exemplos do consultório, sem usar marketing digital, e aplique o método passo a passo."
        ),
        "revisao": (
            "<strong>Objetivo:</strong> Fazer uma revisão rápida e eficiente. "
            "Enfatize os pontos centrais ensinados no curso com clareza. Organize em tópicos curtos ou bullets."
        ),
        "aplicacao": (
            "<strong>Objetivo:</strong> Ensinar como aplicar o conceito no dia a dia do consultório. "
            "Use exemplos realistas e mostre o passo a passo como se estivesse ajudando o aluno a executar a técnica."
        ),
        "correcao": (
            "<strong>Objetivo:</strong> Corrigir gentilmente qualquer erro ou confusão na pergunta do aluno."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Contexto:</strong> O método da Nanda Mac não depende de redes sociais ou tráfego pago."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica ensinado no curso."
        ),
        "health_plan": (
            "<strong>Objetivo:</strong> Ensinar o aluno a montar o **Health Plan** conforme o método da Nanda Mac. "
            "Estruture em Situação Atual, Objetivo, Plano de Tratamento, Previsibilidade de Retorno e Investimento, sempre mantendo o termo **Health Plan** em inglês."
        )
    }

    # Monta o prompt completo
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")
    prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta do aluno:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # Força sempre GPT-4 para máxima qualidade
    modelo_escolhido = "gpt-4"

    # Chama o OpenAI GPT-4 com fallback
    try:
        response = client.chat.completions.create(
            model=modelo_escolhido,
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

    return response.choices[0].message.content
