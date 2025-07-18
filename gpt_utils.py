import os
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
# CONSTANTES DE MENSAGENS
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Parece que sua pergunta ainda não está contemplada nas aulas do curso Consultório High Ticket. "
    "Mas não se preocupe: nosso conteúdo está sempre em expansão! 😊<br><br>"
    "Que tal explorar tópicos relacionados, como 'Health Plan', 'Patient Letter' ou 'Plano de Ação'? "
    "Você pode reformular sua dúvida com base nesses temas ou perguntar sobre qualquer módulo ou atividade, "
    "e eu ficarei feliz em ajudar com o que estiver ao meu alcance."
)
CLOSING_PHRASE = "<br><br>Espero que isso ajude! Qualquer outra dúvida, estou à disposição! 💜"

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
# LEITURA DE ARQUIVOS
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

# Carrega transcrições
try:
    _raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
except FileNotFoundError:
    _raw_txt = ""

# Função de busca em transcrições

def search_transcripts(question: str, max_sentences: int = 3) -> str:
    if not _raw_txt:
        return ""
    key = normalize_key(question)
    sentences = re.split(r'(?<=[\.\!\?])\s+', _raw_txt)
    matches = []
    for sent in sentences:
        norm = normalize_key(sent)
        if all(word in norm for word in key.split() if len(word) > 3):
            matches.append(sent.strip())
        if len(matches) >= max_sentences:
            break
    return "<br>".join(matches) if matches else ""

# Carrega PDFs complementares (opcional)
_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "5.8 - Dossiê 007 - (3)[1].pdf"))
_raw_pdf4 = read_pdf(os.path.join(BASE_DIR, "Papelaria e brindes  lista de links e indicações.pdf"))

# -----------------------------
# PALAVRAS-CHAVE E RESPOSTAS CANÔNICAS
# -----------------------------
TYPE_KEYWORDS = {
    "revisao": ["revisão", "revise", "resumir"],
    "precificacao": ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan": ["health plan", "retorno do investimento", "canva"],
    "capitacao_sem_marketing_digital": ["offline", "sem instagram", "sem anúncios", "sem redes sociais"],
    "aplicacao": ["como aplico", "aplicação", "roteiro"],
    "faq": ["quais", "pergunta frequente"],
    "explicacao": ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao": ["plano de ação", "primeira semana"],
    "guia": ["guia do curso", "passo a passo", "cht21"],
    "dossie": ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"],
    "papelaria": ["jo malone", "importadoras", "cafeteiras", "chocolates", "chás"],
    "playlist": ["playlist", "spotify"]
}

CANONICAL_QA = {
    "oi": ("Olá! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
            "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
            "Posso ajudar em algo hoje? 🥰"),
    "bom dia": ("Bom dia! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
                 "Como posso ajudar você com o método da Nanda hoje? 🥰"),
    "boa tarde": ("Boa tarde! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
                   "Em que posso auxiliar você com o Consultório High Ticket hoje? 🥰"),
    "boa noite": ("Boa noite! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
                  "Estou aqui para ajudar no que precisar. 🥰"),
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo: "
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">"
        "Formulário Health Plan (Canva)</a>. Ele também está disponível na Aula 10.4 do curso."
}
CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

# -----------------------------
# IDENTIDADE E TEMPLATE DINÂMICO
# -----------------------------
identidade = ("<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo "
             "do curso <strong>Consultório High Ticket</strong>. Responda como uma professora experiente, "
             "ajudando o aluno a aplicar o método na prática.")
prompt_variacoes = {
    "explicacao": ("<strong>Objetivo:</strong> Explicar conforme as aulas, com linguagem clara e didática."),
    "faq": ("<strong>Objetivo:</strong> Responder dúvidas frequentes de forma direta e prática.")
}

# -----------------------------
# CLASSIFICADOR E GERADOR DE RESPOSTA
# -----------------------------

def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if any(c in lower for c in CANONICAL_QA_NORMALIZED):
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}


def generate_answer(question: str, context: str = "", history: str = None, tipo_de_prompt: str = None) -> str:
    key = normalize_key(question)
    # 1) Resposta canônica
    for canon, resp in CANONICAL_QA_NORMALIZED.items():
        if canon in key:
            return resp + CLOSING_PHRASE
    # 2) Classifica escopo
    cls = classify_prompt(question)
    # 3) Fallback para fora do escopo
    if cls["scope"] == "OUT_OF_SCOPE":
        snippet = search_transcripts(question)
        if snippet:
            return ("Olá, excelente pergunta!<br><br>" + snippet + CLOSING_PHRASE)
        return OUT_OF_SCOPE_MSG + CLOSING_PHRASE
    # 4) Prompt dinâmico e API
    prompt = identidade + "<br>" + prompt_variacoes.get(cls["type"], "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}";
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}";
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><strong>🧠 Resposta:</strong><br>"
    try:
        r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
    except OpenAIError:
        r = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content + CLOSING_PHRASE
