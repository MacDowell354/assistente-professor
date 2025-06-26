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
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
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
# LEITURA DE ARQUIVOS
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
_raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()

def read_pdf(path):
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "Papelaria e brindes  lista de links e indicações.pdf"))

# combinado apenas para classificação via LLM
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso e "
                "os materiais de Papelaria & Brindes e a playlist Spotify."
            },
            {"role":"user","content":_combined}
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
    "faq":                            ["quais", "pergunta frequente", "duvidas", "dúvidas", "playlist", "spotify"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  [
        "plano de ação", "primeira semana",
        "bloqueios com dinheiro",
        "autoconfianca profissional",
        "nicho de atuacao",
        "valor da consulta",
        "ainda nao tenho pacientes particulares"
    ],
    "guia":                           ["guia do curso", "passo a passo", "cht21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # — Playlist Spotify —
    "onde posso acessar a playlist do consultorio high ticket":
        "Você pode acessar nossa playlist do Consultório High Ticket no Spotify: "
        "<a href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>
        Spotify – Consultório High Ticket</a>.",  
    "qual e o link da playlist recomendada no modulo 4":
        "O link da playlist mencionada na aula 4.17 do Módulo 4 é: "
        "<a href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>
        Spotify – Aula 4.17</a>.",
    "como ouco a playlist do curso":
        "Para ouvir a playlist, basta clicar em “Play” neste link: "
        "<a href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>
        Ouvir Playlist</a>.",
    "em que aula e mencionada a playlist do consultorio high ticket":
        "A playlist é mencionada na <strong>Aula 4.17</strong> do Módulo 4 – A Jornada do Paciente High Ticket.",
    "como encontro a playlist do consultorio high ticket no spotify":
        "Você encontra a playlist buscando “Consultório High Ticket” no Spotify ou acessando diretamente: "
        "<a href='https://open.spotify.com/playlist/5Vop9zNsLcz0pkpD9aLQML?si=vJDC7OfcQXWpTernDbzwHA&nd=1&dlsi=964d4360d35e4b80' target='_blank'>
        Playlist no Spotify</a>."
}

# pré-normaliza as chaves
CANONICAL_QA_NORMALIZED = { normalize_key(k): v for k, v in CANONICAL_QA.items() }

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use linguagem clara e tópicos. Evite genéricos.<br><br>"
    ),
    # demais variações mantidas...
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if lower in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
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
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG
    prompt = identidade + prompt_variacoes.get(cls["type"], "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"
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
