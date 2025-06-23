import os
from openai import OpenAI, OpenAIError

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

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
    # 🔍 Mensagens automáticas
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

    # 📌 Somente estes tipos exigem contexto; os demais usam o template mesmo sem context
    tipos_que_exigem_contexto = {"explicacao", "faq", "revisao", "correcao", "precificacao"}
    if tipo_de_prompt in tipos_que_exigem_contexto and (not context or not context.strip()):
        return OUT_OF_SCOPE_MSG

    # 🆔 Identidade do assistente
    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso <strong>Consultório High Ticket</strong>. "
        "Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
    )

    # 📖 Templates de variações de prompt
    prompt_variacoes = {
        "explicacao": (
            "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
            "com tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula de **Posicionamento High Ticket**.<br><br>"
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
            "<strong>Objetivo:</strong> Corrigir gentilmente qualquer erro ou confusão na pergunta do aluno, "
            "elogiando o esforço e explicando o conceito correto com base no curso."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Objetivo:</strong> Mostrar uma estratégia 100% offline para atrair pacientes de alto valor sem usar Instagram ou anúncios, "
            "baseada no método da Nanda Mac. Use passos práticos e exemplos reais de consultório."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica ensinado no curso Consultório High Ticket. "
            "Use o Health Plan como ferramenta, mostre benefícios e passos para apresentar o valor ao paciente."
        ),
        "health_plan": (
            "<strong>Objetivo:</strong> Ensinar o aluno a montar o **Health Plan** conforme o método da Nanda Mac. "
            "Mantenha o termo **Health Plan** em inglês, pois é o nome da ferramenta. Estruture assim:<br>"
            "➡ **Situação Atual:** Descreva o que o paciente vive hoje — sinais, sintomas e desafios;<br>"
            "➡ **Objetivo:** Defina o resultado esperado com clareza;<br>"
            "➡ **Plano de Tratamento:** Liste passos e recursos concretos;<br>"
            "➡ **Previsibilidade de Retorno:** Explique o follow-up e métricas de progresso;<br>"
            "➡ **Investimento:** Apresente o valor total do **Health Plan** com confiança.<br><br>"
            "Use exemplos práticos de consultório e linguagem direta."
        )
    }

    # 🔧 Monta o prompt completo
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")
    if context and context.strip():
        prompt += f"<br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 🚀 Chama o OpenAI GPT-4 com fallback para 3.5-turbo
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

    return response.choices[0].message.content
