import re
import random
import unicodedata
from openai import OpenAIError
from openai import OpenAI

# Inicialização do cliente da OpenAI
client = OpenAI(api_key="YOUR_API_KEY")

# Mensagens
GREETINGS = [
    "Olá! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!",
    "Oi, que bom te ver aqui!",
    "Olá, seja bem-vindo!"
]

CLOSINGS = [
    "Continue avançando e conte comigo no que precisar.",
    "Fique à vontade para perguntar sempre que quiser evoluir.",
    "Conte comigo sempre que precisar esclarecer algo."
]

OUT_OF_SCOPE_MSG = "Essa dúvida ainda não está contemplada no nosso curso atual. Mas fique tranquilo, já anotei aqui para futuras melhorias!"

# Carregar transcrição
with open("transcricoes.txt", encoding="utf-8") as f:
    _raw_txt = f.read()

# Normalização
NORMALIZATION_FORM = "NFD"


def normalize_key(s: str) -> str:
    return unicodedata.normalize(NORMALIZATION_FORM, s.lower())


# Busca otimizada por temas
def search_transcripts_by_theme(question: str, max_blocks: int = 1, max_length: int = 3000) -> str:
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

    # Limitação de caracteres enviada ao GPT (3000 caracteres ~750 tokens)
    max_characters = 3000
    snippet_curto = snippet[:max_characters] if len(snippet) > max_characters else snippet

    if snippet_curto:
        prompt = (
            "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
            "Responda de forma clara, direta e didática, explicando apenas sobre o tema do trecho abaixo, que foi marcado como importante para a dúvida do aluno. "
            "Dê exemplos reais e simples de como o profissional pode aplicar no consultório físico, usando o método do curso. "
            "Evite repetir definições genéricas e foque na aplicação prática do tema detectado. "
            "Comece com uma saudação curta, explique o conceito, traga exemplos práticos do dia a dia do consultório e incentive o aluno a perguntar mais."
            "\n\nTrecho do curso:\n" + snippet_curto + "\n\n"
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
