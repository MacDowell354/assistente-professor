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
    # 🔧 DEBUG: Tipo de prompt e contexto recebido
    print("🔧 DEBUG – tipo_de_prompt em generate_answer:", tipo_de_prompt)
    print("🔧 DEBUG – contexto recebido (até 200 chars):", context[:200] + ("..." if len(context) > 200 else ""))

    # 🔍 Mensagens automáticas
    termos_mensagem_auto = [
        "mensagem automática", "whatsapp", "resposta automática",
        "fim de semana", "fora do horário", "responder depois", "robô"
    ]
    if any(t in question.lower() for t in termos_mensagem_auto):
        return (
            "Olá, querida! Vamos esclarecer isso com base no que a própria Nanda orienta no curso:<br><br>"
            "📌 A Nanda não recomenda o uso de <strong>mensagens automáticas genéricas</strong> no WhatsApp...<br><br>"
            "Se quiser, posso te ajudar a montar uma mensagem mais humana e acolhedora agora mesmo. Deseja isso?"
        )

    # 📌 Tipos que exigem contexto para não cair em "fora de escopo"
    tipos_que_exigem_contexto = {"explicacao", "faq", "revisao", "correcao", "precificacao"}
    if tipo_de_prompt in tipos_que_exigem_contexto and (not context or not context.strip()):
        return OUT_OF_SCOPE_MSG

    # 🆔 Identidade
    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
        "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
    )

    # 📖 Templates de variações de prompt
    prompt_variacoes = {
        "explicacao": (
            "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
            "com tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula de **Posicionamento High Ticket**.<br><br>"
        ),
        "faq": (
            "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
            "Use exemplos práticos e aplique o método passo a passo."
        ),
        "revisao": (
            "<strong>Objetivo:</strong> Fazer uma revisão rápida e eficiente. Organize em tópicos curtos ou bullets."
        ),
        "aplicacao": (
            "<strong>Objetivo:</strong> Ensinar como aplicar o conceito no dia a dia do consultório, com exemplos realistas."
        ),
        "correcao": (
            "<strong>Objetivo:</strong> Corrigir gentilmente qualquer erro na pergunta, elogiando o esforço."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Objetivo:</strong> Mostrar uma **estratégia 100% offline** para atrair pacientes de alto valor sem usar Instagram ou anúncios, "
            "baseada no método da Nanda Mac. Siga estes passos práticos e use exemplos reais de consultório."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica. Use o Health Plan como ferramenta, "
            "mostre benefícios e passos para apresentar o valor ao paciente."
        ),
        "health_plan": (
            "<strong>Objetivo:</strong> Ensinar o aluno a montar o **Health Plan** conforme o método da Nanda Mac. "
            "Mantenha o termo inglês e estruture:<br>"
            "➡ Situação Atual;<br>➡ Objetivo;<br>➡ Plano de Tratamento; "
            "➡ Previsibilidade de Retorno;<br>➡ Investimento.<br><br>"
        )
    }

    # 🔧 Decidir se inclui contexto no prompt
    if tipo_de_prompt == "capitacao_sem_marketing_digital":
        contexto_para_prompt = ""
    else:
        contexto_para_prompt = (
            f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
            if context and context.strip() else ""
        )

    # 🔧 Monta o prompt completo
    prompt = identidade + prompt_variacoes[tipo_de_prompt] + contexto_para_prompt
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 🚀 Chama o GPT-4 com fallback para 3.5
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
