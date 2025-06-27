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
    raise ValueError("Variável de ambiente OPENAI_API_KEY não encontrada.")
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
    no_accents = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    lower = no_accents.lower()
    alnum = re.sub(r"[^\w\s]", "", lower)
    single_space = re.sub(r"\s+", " ", alnum).strip()
    if single_space.startswith("nanda "):
        single_space = single_space[len("nanda "):]
    return single_space

# -----------------------------
# PALAVRAS-CHAVE PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "faq": ["quais", "pergunta frequente"],
    "health_plan": ["formulario", "canva", "health plan"],
    "checklist": ["checklist", "fase 1", "fase 2", "fase 3"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # Link Health Plan no Canva
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo:<br>"
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?"
        "utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&"
        "utm_source=publishsharelink&mode=preview\" target=\"_blank\">"
        "Formulário Health Plan (Canva)</a>.<br>"
        "Ele também está disponível na Aula 10.4 do curso.",

    # Checklist Consultório High Ticket
    "o que significa implementar health plan para apresentar os valores de tratamentos na fase 1 do checklist":
        "Significa que você deve usar o modelo de Health Plan para detalhar cada opção de tratamento "
        "(protocolos, cirurgias, etc.), expondo claramente investimento e benefícios para o paciente. "
        "Assim, você garante transparência e percepção de valor desde o primeiro contato.",

    "na fase 2 como defino quais brindes high ticket oferecer aos meus melhores pacientes":
        "Escolha brindes que reforcem o posicionamento premium do seu consultório, como kits personalizados "
        "(canecas de cerâmica, velas aromáticas sofisticadas) ou vouchers de experiências exclusivas "
        "(sessão de massagem, avaliação estética). O importante é alinhar o brinde ao perfil “Key Man” "
        "ou “Key Woman” que você deseja fidelizar.",

    "por que retirar o jardim vertical na area de recepcao conforme indicado":
        "O jardim vertical pode gerar distração e poluição visual no ambiente High Ticket. Retirá-lo ajuda "
        "a manter a decoração mais clean e sofisticada, reforçando a percepção de exclusividade e foco no paciente.",

    "qual a importancia de implementar som ambiente com a playlist consultorio high ticket":
        "A trilha sonora certa cria uma atmosfera acolhedora e profissional, melhorando a experiência do paciente "
        "e reforçando seu posicionamento High Ticket. A Playlist Consultório High Ticket foi curada para transmitir "
        "tranquilidade e exclusividade.",

    "como usar o checklist em pdf para acompanhar minhas tarefas concluidas":
        "Você pode baixar o PDF preenchível abaixo e ir marcando cada item à medida que conclui. "
        "Assim, terá um registro visual do seu progresso fase a fase:<br>"
        "📥 <a href=\"/mnt/data/CHECKLISTCONSULTORIOHIGHTICKET.pdf\" target=\"_blank\">"
        "Download do Checklist Consultório High Ticket (PDF preenchível)</a>"
}

CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# IDENTIDADE E TEMPLATE FAQ
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo "
    "do curso Consultório High Ticket. Responda como uma professora experiente, "
    "ajudando o aluno a aplicar o método na prática.<br><br>"
)
prompt_variacoes = {
    "faq": (
        "<strong>Objetivo:</strong> Responder dúvidas frequentes, incluindo links ativos quando aplicável."
    )
}

# -----------------------------
# CLASSIFICADOR
# -----------------------------
def classify_prompt(question: str) -> dict:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in key for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

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
    # 1) Resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Prompt dinâmico
    prompt = identidade + prompt_variacoes.get("faq", "")
    if context:
        prompt += f"<br><strong>Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>Pergunta:</strong><br>{question}<br><br><strong>Resposta:</strong><br>"

    # 4) Fallback GPT-4 / GPT-3.5
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
