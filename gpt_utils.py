import os
import json
import re
import unicodedata
from openai import OpenAI, OpenAIError
from pypdf import PdfReader

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
    "Essa pergunta é muito boa, mas no momento ela está "
    "<strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma "
    "oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar "
    "a inclusão em versões futuras do curso. Enquanto isso, "
    "recomendamos focar nos ensinamentos já disponíveis para ter "
    "os melhores resultados possíveis no consultório."
)

# -----------------------------
# NORMALIZAÇÃO DE CHAVE
# -----------------------------

def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    no_accents = ''.join(ch for ch in nfkd if unicodedata.category(ch) != 'Mn')
    s = no_accents.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("nanda "):
        s = s[len("nanda "):]
    return s

# -----------------------------
# CLASSIFICAÇÃO DE PROMPTS
# -----------------------------
TYPE_KEYWORDS = {
    "faq":        ["quais", "pergunta frequente", "como usar"],
    "checklist":  ["checklist", "fase 1", "fase 2", "fase 3", "fase 4"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # Checklist — Fase 1
    "o que significa implementar health plan para apresentar os valores de tratamentos na fase 1 do checklist":
        "Significa que você deve usar o modelo de Health Plan para detalhar cada opção de tratamento, incluindo cirurgias ou protocolos, expondo investimento e benefícios de forma clara para o paciente. fileciteturn36file0",
    # Checklist — Fase 2
    "na fase 2 como defino quais brindes high ticket oferecer aos meus melhores pacientes":
        "Escolha brindes que reforcem o posicionamento premium do seu consultório, como kits personalizados ou vouchers de experiências exclusivas, alinhados ao perfil Key Man e Key Woman. fileciteturn36file0",
    # Checklist — Fase 3
    "por que retirar o jardim vertical na area de recepcao":
        "O jardim vertical gera distração e ruído visual. Retirá-lo ajuda a manter o ambiente clean e sofisticado, reforçando a percepção de exclusividade. fileciteturn36file0",
    # Checklist — Fase 4
    "qual a importancia de implementar som ambiente com a playlist consultorio high ticket":
        "A trilha sonora certa cria uma atmosfera acolhedora e profissional, melhorando a experiência do paciente e reforçando seu posicionamento High Ticket. fileciteturn36file0",
    # Checklist — PDF preenchível
    "como usar o checklist em pdf para acompanhar minhas tarefas concluídas":
        "Você pode baixar o PDF preenchível abaixo e ir marcando cada item à medida que conclui. Assim, terá um registro visual do seu progresso:<br>"
        "<a href=\"sandbox:/mnt/data/CHECKLISTCONSULTORIOHIGHTICKET.pdf\" target=\"_blank\">🔽 Download do Checklist Consultório High Ticket (PDF preenchível)</a> fileciteturn36file0"](sandbox:/mnt/data/CHECKLISTCONSULTORIOHIGHTICKET.pdf) fileciteturn36file0"
}
CANONICAL_QA_NORMALIZED = { normalize_key(k): v for k, v in CANONICAL_QA.items() }

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)
prompt_variacoes = {
    "faq": (
        "<strong>Objetivo:</strong> Responder dúvidas frequentes de forma direta, incluindo citações e links ativos."
    )
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in key for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "faq"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    # Resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # Classificação de escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # Monta prompt dinâmico
    prompt = identidade + prompt_variacoes.get(cls["type"], "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # Chama OpenAI
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r.choices[0].message.content
