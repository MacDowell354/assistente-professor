import os
import json
import re
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
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# NORMALIZAÇÃO DE CHAVE
# -----------------------------
def normalize_key(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# -----------------------------
# CARREGA TRANSCRIÇÕES E PDFs
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

_raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()

PDF1_PATH = os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf")
_raw_pdf1 = ""
try:
    reader1 = PdfReader(PDF1_PATH)
    _raw_pdf1 = "\n\n".join(page.extract_text() or "" for page in reader1.pages)
except:
    _raw_pdf1 = ""

PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except:
    _raw_pdf2 = ""

# Para classificação (não usado diretamente nas respostas canônicas)
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana) e Guia do Curso, "
                "para servir de base na classificação de prompts."
            },
            {"role": "user", "content": _combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# PALAVRAS-CHAVE PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital":["offline", "sem instagram", "sem anúncios"],
    "aplicacao":                      ["como aplico", "aplicação", "roteiro"],
    "faq":                            ["quais", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "checklist":                      ["checklist", "fase 1", "fase 2", "fase 3", "fase 4", "fase 5"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # — Checklist Consultório High Ticket —
    "nanda o que significa implementar health plan para apresentar os valores de tratamentos na fase 1 do checklist":
        "Significa que você deve usar o modelo de Health Plan para detalhar cada opção de tratamento "
        "(protocolos, cirurgias, etc.), expondo claramente investimento e benefícios para o paciente. "
        "Assim, você garante transparência e percepção de valor desde o primeiro contato.",
    "nanda na fase 2 como defino quais brindes high ticket oferecer aos meus melhores pacientes":
        "Escolha brindes que reforcem o posicionamento premium do seu consultório, como kits personalizados "
        "(canecas de cerâmica, velas aromáticas sofisticadas) ou vouchers de experiências exclusivas "
        "(sessão de massagem, avaliação estética). Alinhe sempre ao perfil “Key Man” ou “Key Woman”.",
    "nanda por que retirar o jardim vertical na area de recepcao conforme indicado":
        "O jardim vertical pode gerar distração e ruído visual no ambiente High Ticket. Retirá-lo mantém "
        "o foco na experiência de exclusividade, com decoração mais clean e sofisticada.",
    "nanda qual a importancia de implementar som ambiente com a playlist consultorio high ticket":
        "A trilha sonora certa cria uma atmosfera acolhedora e profissional. A Playlist Consultório High Ticket "
        "foi curada para transmitir tranquilidade e exclusividade, melhorando a experiência do paciente.",
    "nanda como usar o checklist em pdf para acompanhar minhas tarefas concluidas":
        "Você pode baixar o PDF preenchível abaixo e ir marcando cada item à medida que conclui. Assim, terá "
        "um registro visual do seu progresso fase a fase:<br>"
        "<a href=\"sandbox:/mnt/data/CHECKLISTCONSULTORIOHIGHTICKET.pdf\" target=\"_blank\">"
        "📥 Download do Checklist Consultório High Ticket (PDF preenchível)</a>."
}

# normaliza chaves
CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = question.lower()
    if "exercício" in lower or "exercicios" in lower:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(k in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(question: str, context: str = "", history: str = None) -> str:
    # 1) Resposta canônica
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Fallback de escopo/tipo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Construção de prompt dinâmico
    tipo = cls["type"]
    prompt = (
        "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
        "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
    )
    # Templating básico (pode expandir para cada tipo se desejar)
    prompt += f"<strong>Objetivo:</strong> {tipo.replace('_', ' ').capitalize()}.<br><br>"
    if context:
        prompt += f"<strong>Contexto relevante:</strong><br>{context}<br><br>"
    if history:
        prompt += f"<strong>Histórico anterior:</strong><br>{history}<br><br>"
    prompt += f"<strong>Pergunta:</strong><br>{question}<br><br><strong>Resposta:</strong><br>"

    # 4) Chamada à OpenAI
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
