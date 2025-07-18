import os
import re
import unicodedata
import random
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
# VARIAÇÕES DE SAUDAÇÃO E ENCERRAMENTO
# -----------------------------
GREETINGS = [
    "Olá, doutor! Que bom te ver por aqui! 😊",
    "Oi, que ótima dúvida! Vamos aprender juntos! ✨",
    "Bem-vindo(a) de volta ao seu espaço de crescimento!",
    "Adorei sua pergunta, é bem relevante para sua prática! 🤗",
    "Que bom que você veio perguntar, isso mostra comprometimento! 💬"
]

CLOSINGS = [
    "Qualquer outra dúvida, estou sempre por aqui para te apoiar! 💜",
    "Pode contar comigo para esclarecer o que precisar! Sucesso! 🌷",
    "Estou aqui para ajudar — não hesite em perguntar sempre! ✨",
    "Espero ter esclarecido, até nossa próxima aula! 🤍",
    "Continue perguntando, é assim que você cresce na profissão! 🤗"
]

# -----------------------------
# MENSAGEM DE FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Ainda não temos esse tema nas aulas do curso Consultório High Ticket. Mas vou sinalizar para nossa equipe incluir em breve! "
    "Enquanto isso, recomendo focar no que já temos no curso para conquistar resultados concretos no consultório."
)

# -----------------------------
# NORMALIZAÇÃO DE CHAVE
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# LEITURA DO ARQUIVO DE TRANSCRIÇÕES
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
try:
    _raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
except FileNotFoundError:
    _raw_txt = ""

# -----------------------------
# BUSCA DIDÁTICA POR TRECHOS
# -----------------------------
def search_transcripts(question: str, max_sentences: int = 4) -> str:
    if not _raw_txt:
        return ""
    key = normalize_key(question)
    keywords = [w for w in key.split() if len(w) > 3]
    if not keywords:
        return ""
    sentences = re.split(r'(?<=[\.\!\?])\s+', _raw_txt)
    scored = []
    for sent in sentences:
        norm = normalize_key(sent)
        score = sum(1 for w in keywords if w in norm)
        if score > 0:
            scored.append((score, sent.strip()))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_sentences]]
    return " ".join(top)

# -----------------------------
# GERADOR DE RESPOSTAS DIDÁTICAS
# -----------------------------
def generate_answer(question: str, context: str = "", history: list = None, tipo_de_prompt: str = None) -> str:
    saudacao = random.choice(GREETINGS)
    fechamento = random.choice(CLOSINGS)
    key = normalize_key(question)

    # 1) Busca o trecho relevante
    snippet = search_transcripts(question)

    # 2) Se encontrar trecho, interpreta como professora
    if snippet:
        prompt = (
            f"Você é Nanda Mac.ia, professora experiente do curso Consultório High Ticket. "
            f"Explique o trecho abaixo de maneira clara, passo a passo, com exemplos práticos para médicos, "
            f"usando tom acolhedor e encorajando o aluno a perguntar mais. Comece com saudação calorosa e termine com incentivo.\n\n"
            f"Trecho do curso:\n{snippet}\n\n"
            f"[IMPORTANTE] Não invente nada, só use conteúdo do trecho. Não cite texto literal: ensine, explique e traduza em aula prática."
        )
        try:
            r = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
        except OpenAIError:
            r = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
        explicacao = r.choices[0].message.content.strip()
        return f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"

    # 3) Fora de escopo
    return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
