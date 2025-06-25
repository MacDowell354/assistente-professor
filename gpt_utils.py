import os
import json
import logging
from openai import OpenAI, OpenAIError

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# API KEY
# -----------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")
client = OpenAI(api_key=api_key)

# -----------------------------
# MENSAGEM FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# RESUME TRANSCRIÇÕES (startup)
# -----------------------------
TRANSCRIPT_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")
_raw = open(TRANSCRIPT_PATH, encoding="utf-8").read()
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "Você é um resumidor especialista em educação. "
                "Resuma em até 300 palavras o conteúdo do curso “Consultório High Ticket” "
                "para servir de base na classificação de escopo e tipo de prompt."
            )},
            {"role": "user", "content": _raw}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
    logger.info("Resumo do curso carregado com sucesso.")
except Exception as e:
    COURSE_SUMMARY = ""
    logger.warning("Falha ao resumir transcricoes: %s", e)

# -----------------------------
# PALAVRAS-CHAVE POR TIPO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revisao", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificacao", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "valor do health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital":["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao":                      ["como aplico", "aplicação", "aplico", "roteiro"],
    "faq":                            ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"]
}

# -----------------------------
# TEMPLATES E IDENTIDADE
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas…<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder dúvida frequente…"
    ),
    "revisao": (
        "<strong>Objetivo:</strong> Fazer revisão rápida do método de precificação estratégica em 6 bullets…<br><br>"
    ),
    "aplicacao": (
        "<strong>Objetivo:</strong> Aplicar roteiro de atendimento High Ticket na primeira consulta (6 bullets)…<br><br>"
    ),
    "correcao": (
        "<strong>Objetivo:</strong> Corrigir gentilmente confusões…<br><br>"
    ),
    "capitacao_sem_marketing_digital": (
        "<strong>Objetivo:</strong> Estratégia 100% offline para atrair pacientes de alto valor sem Instagram…<br><br>"
    ),
    "precificacao": (
        "<strong>Objetivo:</strong> Explicar precificação estratégica, mantendo **Health Plan** em inglês…<br><br>"
    ),
    "health_plan": (
        "<strong>Objetivo:</strong> Estruturar apresentação de valor do **Health Plan**, incluindo benefícios tangíveis e histórias de sucesso…<br><br>"
    )
}

# -----------------------------
# CLASSIFICADOR
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()
    for tipo, keys in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keys):
            return {"scope": "IN_SCOPE", "type": tipo}

    # fallback via GPT
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda **apenas** um JSON com duas chaves:\n"
        "  • scope: 'IN_SCOPE' ou 'OUT_OF_SCOPE'\n"
        "  • type: nome de um template (ex: 'explicacao', 'health_plan', …)\n\n"
        f"Resumo do curso:\n{COURSE_SUMMARY}\n\n"
        f"Pergunta:\n{question}\n\n"
        "Exemplo de resposta:\n"
        '{ "scope": "IN_SCOPE", "type": "health_plan" }'
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except Exception as e:
        logger.warning("Classifier fallback falhou: %s", e)
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# GERAÇÃO DE RESPOSTA
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str | None = None
) -> str:
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    tipo = cls["type"]
    template = prompt_variacoes.get(tipo, prompt_variacoes["explicacao"])

    ctx = (
        f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
        if context.strip() and tipo != "capitacao_sem_marketing_digital" else ""
    )
    hist = (
        f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
        if history else ""
    )

    full_prompt = (
        identidade
        + template
        + ctx
        + f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"
        + hist
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}]
        )
        return resp.choices[0].message.content.strip()

    except OpenAIError as e:
        msg = str(e).lower()
        if "rate limit" in msg:
            return "Limite de requisições atingido. Tente novamente mais tarde."
        if "invalid api key" in msg or "authentication" in msg:
            return "Erro de autenticação com o serviço de IA."
        logger.error("OpenAIError: %s", e)
        return "Erro ao obter resposta da IA."
    except Exception as e:
        logger.exception("Erro inesperado ao gerar resposta: %s", e)
        return "Erro interno ao processar sua solicitação."
