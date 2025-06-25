import os
import json
import logging
from openai import OpenAI, OpenAIError
from openai.error import AuthenticationError, RateLimitError

# -----------------------------
# CONFIGURAÇÃO DE LOG
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# CONFIGURAÇÃO DE AMBIENTE
# -----------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")
client = OpenAI(api_key=api_key)

# -----------------------------
# MENSAGEM PADRÃO PARA FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# MAPEAMENTO DE KEYWORDS
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
# CARREGA E RESUME TRANSCRIÇÕES (1× NO STARTUP)
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
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

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
        "<strong>Objetivo:</strong> Fazer uma revisão rápida dos pontos centrais do método de precificação estratégica. "
        "Use exatamente seis bullets, cada um iniciando com verbo de ação e título em negrito: "
        "**Identificar Pacientes Potenciais**, **Determinar Valores**, **Elaborar o Health Plan**, "
        "**Preparar a Apresentação**, **Comunicar o Valor** e **Monitorar Resultados**. "
        "Após o título de cada bullet, adicione uma breve explicação de uma linha. "
        "E **certifique-se de mencionar o benefício de dobrar o faturamento e fidelizar pacientes** em pelo menos dois desses bullets.<br><br>"
    ),
    "aplicacao": (
        "<strong>Objetivo:</strong> Aplicar o roteiro de atendimento High Ticket na primeira consulta. "
        "Use exatamente seis bullets, cada um iniciando com verbo de ação e estes títulos em negrito:<br>"
        "➡ **Abertura da Consulta:** Garanta acolhimento profissional e empatia.<br>"
        "➡ **Mapear Expectativas:** Pergunte objetivos e preocupações do paciente.<br>"
        "➡ **Elaborar Health Plan:** Explique o plano personalizado e investimento.<br>"
        "➡ **Validar Compromisso:** Confirme entendimento e mencione dobrar faturamento.<br>"
        "➡ **Usar Two-Options:** Ofereça duas opções de pacote.<br>"
        "➡ **Agendar Follow-up:** Marque retorno para fidelizar.<br><br>"
    ),
    "correcao": (
        "<strong>Objetivo:</strong> Corrigir gentilmente qualquer confusão ou prática equivocada, "
        "apontando a abordagem correta conforme o método High Ticket.<br><br>"
    ),
    "capitacao_sem_marketing_digital": (
        "<strong>Objetivo:</strong> Mostrar uma **estratégia 100% offline** para atrair pacientes "
        "de alto valor sem usar Instagram ou anúncios:<br>"
        "➡ Envie convites VIP impressos;<br>"
        "➡ Faça mini-palestras em parcerias;<br>"
        "➡ Envie cartas personalizadas;<br>"
        "➡ Mensagens de voz via WhatsApp;<br>"
        "➡ Depoimentos impressos;<br>"
        "➡ Programa “Indique um amigo VIP”.<br><br>"
        "Isso <strong>dobra seu faturamento</strong> sem redes sociais."
    ),
    "precificacao": (
        "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica. "
        "Use bullets com **Health Plan** em inglês, mencionando dobrar faturamento e fidelizar.<br><br>"
    ),
    "health_plan": (
        "<strong>Objetivo:</strong> Estruturar a apresentação de valor do **Health Plan**. "
        "Use passos sequenciais, benefícios tangíveis e histórias de sucesso.<br><br>"
    )
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
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
        "  • type: nome de um template (ex: 'explicacao', 'health_plan', ...)\n\n"
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
# GERA A RESPOSTA FINAL
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

    ctx = f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>" if context.strip() and tipo != "capitacao_sem_marketing_digital" else ""
    hist = f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>" if history else ""

    prompt = (
        identidade
        + template
        + ctx
        + f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"
        + hist
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except AuthenticationError:
        return "Erro de autenticação com o serviço de IA."
    except RateLimitError:
        return "Limite de requisições atingido. Tente novamente mais tarde."
    except OpenAIError as e:
        logger.error("Erro OpenAI: %s", e)
        return "Erro ao obter resposta da IA."
    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return "Erro interno ao processar sua solicitação."

    return resp.choices[0].message.content.strip()
