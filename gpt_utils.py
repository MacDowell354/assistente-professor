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
    "Use linguagem acolhedora e didática: inicie com uma saudação variada, explique passo a passo "
    "e finalize com um encerramento acolhedor. Todas as respostas devem ser em português e baseadas nas transcrições do curso."
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

def search_transcripts(question: str, max_sentences: int = 3) -> str:
    """
    Recupera até max_sentences sentenças mais relevantes de transcricoes.txt, 
    ordenadas pelo número de palavras-chave da pergunta presentes.
    """
    if not _raw_txt:
        return ""
    # Extrair palavras-chave significativas
    key = normalize_key(question)
    keywords = [w for w in key.split() if len(w) > 3]
    if not keywords:
        return ""
    # Dividir em sentenças
    sentences = re.split(r'(?<=[\.\!\?])\s+', _raw_txt)
    scored = []
    # Pontuar cada sentença
    for sent in sentences:
        norm = normalize_key(sent)
        score = sum(1 for w in keywords if w in norm)
        if score > 0:
            scored.append((score, sent.strip()))
    # Ordenar por pontuação decrescente
    scored.sort(key=lambda x: x[0], reverse=True)
    # Selecionar top
    top = [s for _, s in scored[:max_sentences]]
    return "<br>".join(top)

# -----------------------------
# DICIONÁRIO CANÔNICO
# -----------------------------
CANONICAL_QA = {
    "como informar uma atualizacao de valor de consulta sem perder credibilidade":
        "No momento de reagendar, siga estes passos:<br>"
        "1. Reforce o histórico de resultados: “Desde que começamos, você já melhorou X%…”<br>"
        "2. Explique o aumento como investimento em atualizações e tecnologia.<br>"
        "3. Ofereça opções de pagamento: parcelamento ou condições especiais por tempo limitado.<br><br>"
        "Exemplo: “Nossa consulta agora é R$ 350, pois incluí novas técnicas de avaliação… Prefere Pix, cartão ou parcelamento em até 3x?”",
    "como devo decorar meu consultorio e me vestir para nao afastar o paciente high ticket":
        "Decoração: espaços clean, móveis de linhas retas, cores neutras (branco, bege, cinza).<br>"
        "Perfume: fragrâncias leves e universais (ex.: Jo Malone “Lime Basil & Mandarin” ou Giovanna Baby).<br>"
        "Uniforme: jaleco branco clássico sem detalhes, camisa social clara e calça de corte tradicional (sapato social ou scarpin neutro).",
    # Outras entradas canônicas...
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

    # 2) Fallback por busca nas transcrições
    snippet = search_transcripts(question)
    if snippet:
        # Reescrever de forma didática
        prompt = (
            f"Você é Nanda Mac.ia, professora didática. Reescreva o seguinte trecho do curso em suas próprias palavras, "
            f"explicando passo a passo, adicionando exemplos práticos e perguntando se faz sentido para o aluno.\n\n"  
            f"Trecho:\n{snippet}"
        )
        try:
            r = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
        except OpenAIError:
            r = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
        content = r.choices[0].message.content.strip()
        return f"{saudacao}<br><br>{content}<br><br>{fechamento}"

    # 3) Fora de escopo
    return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
