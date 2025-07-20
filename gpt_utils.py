import os
import re
import unicodedata
import random
from openai import OpenAI, OpenAIError

# CONFIGURAÇÃO DE AMBIENTE
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")
client = OpenAI(api_key=api_key)

# SAUDAÇÕES NEUTRAS
GREETINGS = [
    "Olá, tudo bem?",
    "Que bom te ver por aqui!",
    "Bem-vindo(a) de volta!",
    "Olá, seja bem-vindo(a)!"
]

CLOSINGS = [
    "Se tiver mais dúvidas, estou à disposição para ajudar.",
    "Conte comigo sempre que quiser esclarecer algo.",
    "Fique à vontade para perguntar sempre que quiser evoluir.",
    "Sucesso na sua jornada, até breve!",
    "Continue avançando e conte comigo no que precisar."
]

OUT_OF_SCOPE_MSG = (
    "Ainda não temos esse tema nas aulas do curso Consultório High Ticket. "
    "Vou sinalizar para a equipe incluir em breve! Enquanto isso, foque no que já está disponível para conquistar resultados concretos no consultório."
)

# NORMALIZAÇÃO DE CHAVE
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# LEITURA DO ARQUIVO DE TRANSCRIÇÕES
BASE_DIR = os.path.dirname(__file__)
try:
    _raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
except FileNotFoundError:
    _raw_txt = ""

# BUSCA POR BLOCO TEMÁTICO (COM LIMITE DE CARACTERES)
def search_transcripts_by_theme(question: str, max_blocks: int = 2, max_length: int = 3000) -> str:
    if not _raw_txt:
        return ""
    key = normalize_key(question)
    keywords = [w for w in key.split() if len(w) > 3]

    pattern = re.compile(r'\[TEMA:([^\]]+)\](.*?)(?=\[TEMA:|\Z)', re.DOTALL | re.IGNORECASE)
    blocks = pattern.findall(_raw_txt)

    scored = []
    for tagstr, content in blocks:
        tags = [normalize_key(t) for t in tagstr.split(',')]
        tag_score = sum(1 for w in keywords for t in tags if w in t)
        content_score = sum(1 for w in keywords if w in normalize_key(content))
        total_score = tag_score * 3 + content_score
        if total_score > 0:
            scored.append((total_score, content.strip()))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_content = " ".join([s for _, s in scored[:max_blocks]])

    return top_content[:max_length]

# GERADOR DE RESPOSTAS DIDÁTICAS (COM LIMITE DE CONTEXTO)
def generate_answer(
    question: str,
    context: str = "",
    history: list = None,
    tipo_de_prompt: str = None,
    is_first_question: bool = True
) -> str:
    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(question)

    if snippet:
        prompt = (
            "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
            "Responda de forma clara, direta e didática, explicando apenas sobre o tema do trecho abaixo, que foi marcado como importante para a dúvida do aluno. "
            "Dê exemplos reais e simples de como o profissional pode aplicar no consultório físico, usando o método do curso. "
            "Evite repetir definições genéricas e foque na aplicação prática do tema detectado. "
            "Comece com uma saudação curta, explique o conceito, traga exemplos práticos do dia a dia do consultório e incentive o aluno a perguntar mais."
            "\n\nTrecho do curso:\n" + snippet + "\n\n"
            "[IMPORTANTE] Foque só no tema detectado na tag e seja objetivo e prático."
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
        if saudacao:
            return f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"
        else:
            return f"{explicacao}<br><br>{fechamento}"

    if saudacao:
        return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
    else:
        return f"{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
