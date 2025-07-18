import os
import re
import unicodedata
import random
from openai import OpenAI, OpenAIError

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
    "Olá, doutor!",
    "Oi, doutor!",
    "Olá, tudo bem?",
    "Oi, que bom te ver aqui!",
    "Olá, seja bem-vindo!"
]

CLOSINGS = [
    "Se tiver mais dúvidas, estou à disposição para te ajudar.",
    "Conte comigo sempre que precisar esclarecer algo.",
    "Fique à vontade para perguntar sempre que quiser evoluir.",
    "Sucesso na sua jornada, até breve!",
    "Continue avançando e conte comigo no que precisar."
]

# -----------------------------
# MENSAGEM DE FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Ainda não temos esse tema nas aulas do curso Consultório High Ticket. "
    "Vou sinalizar para a equipe incluir em breve! Enquanto isso, foque no que já está disponível para conquistar resultados concretos no consultório."
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

    # 1) Busca o trecho relevante
    snippet = search_transcripts(question)

    # 2) Se encontrar trecho, interpreta como professora, de forma objetiva e prática
    if snippet:
        prompt = (
            "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
            "Responda de forma clara, direta e didática, explicando apenas sobre o termo perguntado (exemplo: reciprocidade). "
            "Dê exemplos reais e simples de como o médico pode aplicar no consultório físico, como pós-consulta, contato humanizado, bilhete de agradecimento, entrega de material ou dica personalizada. "
            "Evite exemplos digitais (blog, YouTube) e foque em atitudes presenciais e no relacionamento real com o paciente. "
            "Deixe claro que esse tipo de atitude faz parte do método Consultório High Ticket. "
            "Comece com saudação curta, explique o conceito, traga exemplos práticos do dia a dia do consultório e incentive o aluno a perguntar mais."
            "\n\nTrecho do curso:\n" + snippet + "\n\n"
            "[IMPORTANTE] Foque apenas no termo da dúvida, seja objetivo e prático, e não repita introduções institucionais."
        )
        try:
            r = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
        except OpenAIError:
            r = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
        explicacao = r.choices[0].message.content.strip()
        return f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"

    # 3) Fora de escopo
    return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
