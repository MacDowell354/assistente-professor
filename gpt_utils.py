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
    "Que ótima dúvida! 😊",
    "Olá, excelente pergunta! 🌟",
    "Adorei sua pergunta! 🤗",
    "Ótima colocação! ✨",
    "Que bom que veio perguntar isso! 💬"
]

CLOSINGS = [
    "Qualquer outra dúvida, estou por aqui! 💜",
    "Fico à disposição para ajudar no que precisar! 🌷",
    "Conte sempre comigo — sucesso nos seus atendimentos! ✨",
    "Espero que tenha ajudado. Até a próxima! 🤍",
    "Estou aqui para o que você precisar. Um abraço! 🤗"
]

# -----------------------------
# CONSTANTES DE MENSAGENS
# -----------------------------
SYSTEM_PROMPT = (
    "Você é Nanda Mac.ia, professora virtual experiente no curso Consultório High Ticket. "
    "Use linguagem acolhedora e didática: inicie com uma saudação variada de GREETINGS, "
    "explique passo a passo como uma professora e finalize com um encerramento de CLOSINGS. "
    "Todas as respostas devem ser em português e baseadas nas transcrições do curso."
)
OUT_OF_SCOPE_MSG = (
    "Parece que sua pergunta ainda não está contemplada nas aulas do curso Consultório High Ticket. "
    "Mas não se preocupe: nosso conteúdo está sempre em expansão! 😊<br><br>"
    "Que tal explorar tópicos relacionados, como 'Health Plan', 'Patient Letter' ou 'Plano de Ação'? "
    "Você pode reformular sua dúvida com base nesses temas ou perguntar sobre qualquer módulo ou atividade, "
    "e eu ficarei feliz em ajudar com o que estiver ao meu alcance."
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
# LEITURA DE TRANSCRIÇÕES
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
try:
    _raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
except FileNotFoundError:
    _raw_txt = ""

# -----------------------------
# FUNÇÃO DE BUSCA POR TRECHOS
# -----------------------------

def search_transcripts(question: str, max_sentences: int = 5) -> str:
    if not _raw_txt:
        return ""
    key = normalize_key(question)
    keywords = [w for w in key.split() if len(w) > 3]
    sentences = re.split(r'(?<=[\.\!\?])\s+', _raw_txt)
    matches = []
    for sent in sentences:
        norm = normalize_key(sent)
        if any(word in norm for word in keywords):
            matches.append(sent.strip())
        if len(matches) >= max_sentences:
            break
    return "<br>".join(matches) if matches else ""

# -----------------------------
# RESPOSTAS CANÔNICAS
# -----------------------------
CANONICAL_QA = {
    # Senso Estético
    "como devo decorar meu consultorio e me vestir para nao afastar o paciente high ticket":
        "Decoração: espaços clean, móveis de linhas retas, cores neutras (branco, bege, cinza).<br>"
        "Perfume: fragrâncias leves e universais (Jo Malone “Lime Basil & Mandarin” ou Giovanna Baby).<br>"
        "Uniforme: jaleco branco clássico sem detalhes, camisa social clara e calça de corte tradicional (sapato social ou scarpin neutro).",
    # Gatilho da Reciprocidade
    "qual a melhor forma de usar o gatilho da reciprocidade para fidelizar meus pacientes":
        "O gatilho da reciprocidade funciona assim: sempre que você oferece algo de valor antes mesmo do paciente pagar, ele se sente motivado a retribuir. No Consultório High Ticket, você pode:<br>"
        "• Enviar materiais educativos grátis (e-book, checklist) após a primeira consulta.<br>"
        "• Oferecer uma avaliação de cortesia de um item extra (ex.: avaliação postural rápida).<br>"
        "• Dar uma amostra de um protocolo complementar (ex.: um mini-exercício ou orientação nutricional).<br><br>"
        "Depois, quando for propor seu plano principal, o paciente já estará predisposto a aceitar.",
}
CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

# -----------------------------
# GERAÇÃO DE RESPOSTA
# -----------------------------

def generate_answer(question: str, context: str = "", history: list = None, tipo_de_prompt: str = None) -> str:
    saudacao = random.choice(GREETINGS)
    fechamento = random.choice(CLOSINGS)
    key = normalize_key(question)

    # 1) Resposta canônica
    for canon, resp in CANONICAL_QA_NORMALIZED.items():
        if canon in key:
            return f"{saudacao}<br><br>{resp}<br><br>{fechamento}"

    # 2) Fallback via transcrições
    snippet = search_transcripts(question)
    if snippet:
        return f"{saudacao}<br><br>{snippet}<br><br>{fechamento}"

    # 3) Fora de escopo
    return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
