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
# NORMALIZAÇÃO DE CHAVE (removendo acentos)
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# LEITURA DE ARQUIVOS PDF (resumido)
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def read_pdf(path):
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

_raw_txt  = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "5.8 - Dossiê 007 - (3)[1].pdf"))

_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso e Dossiê 007."
            },
            {"role":"user","content":_combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# PERGUNTAS CANÔNICAS
# -----------------------------
CANONICAL_QA = {
    "como entro na comunidade high ticket":
        "A Comunidade High Ticket Doctors está dentro da plataforma do curso. Assim que você receber o e-mail com o título “Chegou seu acesso”, cadastre sua senha. Depois de logado, preencha seu perfil e entre na Comunidade para tirar dúvidas sobre o método, fazer networking e participar das oficinas.",

    "como faco para acessar a comunidade high ticket doctors":
        "A Comunidade High Ticket Doctors está dentro da plataforma do curso. Assim que você receber o e-mail com o título “Chegou seu acesso”, cadastre sua senha. Depois de logado, preencha seu perfil e entre na Comunidade para tirar dúvidas sobre o método, fazer networking e participar das oficinas."
}

# -----------------------------
# PRÉ-NORMALIZAÇÃO
# -----------------------------
CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# CLASSIFICAÇÃO DO TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if lower in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# GERADOR DE RESPOSTA
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    return OUT_OF_SCOPE_MSG
