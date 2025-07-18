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
    "Olá, que bom ver você por aqui! 😊",
    "Oi! Espero que seu dia esteja ótimo! 🌟",
    "Bem-vindo de volta! Como posso ajudar hoje? 🩺",
    "Oi, tudo bem? Vamos lá, qual a sua dúvida? 💬",
    "Olá! Conte comigo para o que precisar! 🤗"
]

CLOSINGS = [
    "Qualquer outra dúvida, estou por aqui! 💜",
    "Fico à disposição para ajudar no que precisar! 🌷",
    "Conte sempre comigo — sucesso nos seus atendimentos! ✨",
    "Espero ter ajudado. Até a próxima! 🤍",
    "Estou aqui para o que você precisar. Um abraço! 🤗"
]

# -----------------------------
# CONSTANTES DE MENSAGENS
# -----------------------------
SYSTEM_PROMPT = (
    "Você é Nanda Mac.ia, professora virtual experiente no curso Consultório High Ticket. "
    "Use linguagem acolhedora e didática: ofereça saudações variadas, explique passo a passo "
    "e finalize com uma frase de encerramento acolhedora. Todas as respostas devem ser em português."
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
# FUNÇÃO DE BUSCA
# -----------------------------
def search_transcripts(question: str, max_sentences: int = 3) -> str:
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
TYPE_KEYWORDS = {
    "revisao": ["revisão", "revise", "resumir"],
    "precificacao": ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan": ["health plan", "retorno do investimento", "canva"],
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
    # Senso Estético High Ticket (Módulo 2)
    "como devo decorar meu consultorio e me vestir para nao afastar o paciente high ticket":
        "Decoração: espaços clean, móveis de linhas retas, cores neutras (branco, bege, cinza). "
        "Sem poluição visual de logos, quadriculados ou ostentação de marcas.<br><br>"
        "Fragrância: fragrâncias leves e universais (ex.: Jo Malone “Lime Basil & Mandarin” ou Giovanna Baby), "
        "nada muito doce ou intenso que possa causar enjoo.<br><br>"
        "Uniforme e traje pessoal:<br>"
        "• Jaleco branco clássico, sem rendas, mangas bufantes ou logos.<br>"
        "• Para homem: camisa social clara + calça de corte tradicional + sapato social ou mocassim discreto.<br>"
        "• Para mulher: camisa social branca ou tons pastel + calça ou saia de corte clássico + sapato fechado ou scarpin neutro.",
    # Gatilho da Reciprocidade (Módulo 3.6)
    "qual a melhor forma de usar o gatilho da reciprocidade para fidelizar meus pacientes":
        "O gatilho da reciprocidade consiste em oferecer algo de valor antes mesmo do paciente pagar, "
        "para que ele sinta vontade de retribuir seu cuidado. Por exemplo: enviar um e-book ou checklist educativo "
        "após a consulta, oferecer uma avaliação rápida de cortesia (como avaliação postural) ou disponibilizar um "
        "mini-protocolo gratuito. Assim, quando você apresentar seu plano principal, o paciente já estará predisposto "
        "a aceitar essa retribuição.",
    # Exemplo Prático de Reciprocidade
    "pode me dar um exemplo pratico":
        "Claro! Por exemplo, após a consulta, você pode enviar ao paciente um checklist personalizado de exercícios "
        "ou dicas nutricionais por e-mail. Ou ainda oferecer uma avaliação rápida de cortesia (avaliação postural) na próxima sessão. "
        "Esse gesto simples demonstra cuidado e faz o paciente se sentir inclinado a retribuir contratando o plano completo.",
    # Medo de cobrar mais
    "supero o medo de cobrar mais pelos meus atendimentos sem parecer mercenario":
        "Entender que dinheiro resolve muitos problemas — desde investir em atualizações profissionais até permitir "
        "que você dedique mais tempo ao descanso — é o primeiro passo para quebrar esse bloqueio. Lembre-se: quanto "
        "mais você ganha, mais pessoas você pode ajudar, seja doando horas de atendimento social ou empregando "
        "colaboradores em seu consultório. Portanto, ao apresentar seus novos valores, explique ao paciente que esse "
        "ajuste permite oferecer atendimentos mais seguros, atualizados e personalizados — e que isso, na prática, é um ganho "
        "direto para o cuidado dele.",
    # Gavitigo da Escassez (Módulo 1.7.5)
    "como garantir que meus pacientes nao faltem ou adiem sem aviso":
        "Evite plataformas de agendamento que deixem “buracos” visíveis em sua agenda: isso passa a impressão de "
        "disponibilidade total e incentiva o paciente a adiar. Use o gatilho da escassez:<br><br>"
        "“Tenho apenas dois horários abertos para novas consultas nas próximas duas semanas. Se quiser garantir seu "
        "atendimento, posso encaixá-lo na terça ou na quinta-feira.”<br><br>"
        "Assim, você demonstra que seu tempo é valioso, aumenta a percepção de prioridade e reduz faltas."
}
CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

# -----------------------------
# CLASSIFICADOR E GERADOR DE RESPOSTA
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if any(canon in lower for canon in CANONICAL_QA_NORMALIZED):
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

def generate_answer(question: str, context: str = "", history: list = None, tipo_de_prompt: str = None) -> str:
    saudacao = random.choice(GREETINGS)
    fechamento = random.choice(CLOSINGS)
    key = normalize_key(question)
    # 1) Resposta canônica
    for canon, resp in CANONICAL_QA_NORMALIZED.items():
        if canon in key:
            return f"{saudacao}<br><br>{resp}<br><br>{fechamento}"
    # 2) Classificação de escopo
    cls = classify_prompt(question)
    # 3) Fallback fora de escopo
    if cls["scope"] == "OUT_OF_SCOPE":
        snippet = search_transcripts(question)
        if snippet:
            return f"{saudacao}<br><br>{snippet}<br><br>{fechamento}"
        return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
    # 4) Prompt dinâmico
    system_msg = {"role": "system", "content": SYSTEM_PROMPT}
    parts = []
    if context:
        parts.append(f"📚 Contexto:\n{context}")
    if history:
        parts.append("📜 Histórico:\n" + "\n".join(item['ai'] for item in history))
    parts.append(f"🤔 Pergunta:\n{question}")
    user_msg = {"role": "user", "content": "\n\n".join(parts)}
    # 5) Chamada ao OpenAI
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[system_msg, user_msg],
            temperature=0.7,
            max_tokens=500
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_msg, user_msg],
            temperature=0.7,
            max_tokens=500
        )
    answer = r.choices[0].message.content.strip()
    return f"{saudacao}<br><br>{answer}<br><br>{fechamento}"
