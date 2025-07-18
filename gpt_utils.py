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
# SAUDAÇÕES NEUTRAS
# -----------------------------
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
# DETECÇÃO DE PERGUNTA COMPLEMENTAR
# -----------------------------
COMPLEMENTAR_TERMS = [
    "exemplo", "exemplos", "me mostre", "pode detalhar", "me explica melhor", "na prática", "como aplicar", "mostre na prática"
]
def is_complementary_question(question: str) -> bool:
    q = normalize_key(question)
    return any(term in q for term in COMPLEMENTAR_TERMS) or len(q.split()) < 5

# -----------------------------
# GERADOR DE RESPOSTAS DIDÁTICAS
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: list = None,
    tipo_de_prompt: str = None,
    is_first_question: bool = True,
    last_question: str = ""
) -> str:
    # Detecta se a pergunta é complementar, baseada no texto
    complementary = is_complementary_question(question)
    saudacao = random.choice(GREETINGS) if (is_first_question and not complementary) else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts(question)

    # Prompt para resposta NORMAL (com explicação e exemplos)
    base_prompt = (
        "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
        "Responda de forma clara, direta e didática, explicando apenas sobre o termo perguntado (exemplo: reciprocidade). "
        "Dê exemplos reais e simples de como o profissional pode aplicar no consultório físico, como pós-consulta, contato humanizado, bilhete de agradecimento, entrega de material ou dica personalizada. "
        "Evite exemplos digitais (blog, YouTube) e foque em atitudes presenciais e no relacionamento real com o paciente. "
        "Deixe claro que esse tipo de atitude faz parte do método Consultório High Ticket. "
        "Comece com uma saudação curta, explique o conceito, traga exemplos práticos do dia a dia do consultório e incentive o aluno a perguntar mais."
        "\n\nTrecho do curso:\n" + snippet + "\n\n"
        "[IMPORTANTE] Foque apenas no termo da dúvida, seja objetivo e prático, e não repita introduções institucionais."
    )

    # Prompt para resposta COMPLEMENTAR (só exemplos ou detalhamento)
    complementary_prompt = (
        "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
        "O aluno acabou de receber uma explicação sobre o termo acima. Agora ele pediu exemplos práticos, detalhamento ou aplicação. "
        "Responda apenas trazendo exemplos práticos e simples de como aplicar esse conceito no consultório físico, sem repetir definição, saudação ou introdução. "
        "Foque apenas em exemplos reais, sugestões rápidas, frases prontas ou ideias para o dia a dia do consultório."
        "\n\nTrecho do curso:\n" + snippet + "\n\n"
        "[IMPORTANTE] Não repita o conceito. Traga só exemplos, dicas ou frases aplicáveis."
    )

    prompt = complementary_prompt if complementary else base_prompt

    if snippet:
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
