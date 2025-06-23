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
    termos_mensagem_auto = [
        "mensagem automática", "whatsapp", "resposta automática",
        "fim de semana", "fora do horário", "responder depois", "robô"
    ]
    if any(t in question.lower() for t in termos_mensagem_auto):
        return (
            "Olá, querida! Vamos esclarecer isso com base no que a própria Nanda orienta no curso:<br><br>"
            "📌 A Nanda não recomenda o uso de <strong>mensagens automáticas genéricas</strong> no WhatsApp..."
        )

    # **Somente estes tipos exigem contexto**; os demais (incluindo 'capitacao_sem_marketing_digital' e 'health_plan')
    # usam o template mesmo sem context.
    tipos_que_exigem_contexto = {"explicacao", "faq", "revisao", "correcao", "precificacao"}
    if tipo_de_prompt in tipos_que_exigem_contexto and (not context or not context.strip()):
        return OUT_OF_SCOPE_MSG

    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso <strong>Consultório High Ticket</strong>.<br><br>"
    )

    prompt_variacoes = {
        "explicacao": "...",  # seus templates existentes
        "faq": "...",
        "revisao": "...",
        "aplicacao": "...",
        "correcao": "...",
        "capitacao_sem_marketing_digital": (
            "<strong>Contexto:</strong> O método da Nanda Mac <u>não depende de redes sociais ou tráfego pago</u>. "
            "Explique como o aluno pode atrair pacientes de alto valor **sem usar Instagram ou anúncios**..."
        ),
        "precificacao": "...",
        "health_plan": "..."  # seu template de Health Plan em inglês
    }

    # Montagem do prompt
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")
    if context:
        prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    modelo_escolhido = "gpt-4"
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
