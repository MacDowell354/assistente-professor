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
# DICIONÁRIO CANÔNICO
# -----------------------------
CANONICAL_QA = {
    # Situações com resposta fixa
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
    "qual a melhor forma de usar o gatilho da reciprocidade para fidelizar meus pacientes":
        "Encontre formas de oferecer valor antecipado: envie materiais educativos grátis (e-book, checklist) após a primeira consulta; ofereça avaliação de cortesia (ex.: avaliação postural rápida); dê amostras de protocolos complementares (mini-exercícios). Assim, o paciente se sente inclinado a retribuir contratando o plano principal.",
    "pode me dar um exemplo pratico":
        "Por exemplo, após a consulta, envie um checklist personalizado de exercícios ou dicas nutricionais por e-mail. Ou ofereça uma avaliação rápida de cortesia (avaliação postural). Esses gestos simples demonstram cuidado e incentivam o paciente a retribuir contratando o plano completo.",
    "posso enviar a patient letter em formato digital ou preciso ser manuscrita":
        "– Digital: prático, rápido para colegas e pacientes; perfeito para integrar sistemas.<br>"
        "– Manuscrita: transmite cuidado extra, mas leva mais tempo e pode ficar ilegível.<br>"
        "No High Ticket, você pode misturar: envie digitalmente logo após a consulta e, em ocasiões especiais (homenagem, mudança de protocolo), entregue uma versão manuscrita.",
}
CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

# -----------------------------
# GERAÇÃO DE RESPOSTA INTELIGENTE
# -----------------------------

def generate_answer(question: str, context: str = "", history: list = None, tipo_de_prompt: str = None) -> str:
    saudacao = random.choice(GREETINGS)
    fechamento = random.choice(CLOSINGS)
    key = normalize_key(question)

    # 1) Resposta canônica
    for canon, resp in CANONICAL_QA_NORMALIZED.items():
        if canon in key:
            return f"{saudacao}<br><br>{resp}<br><br>{fechamento}"

    # 2) Busca e interpretação via transcrições
    snippet = search_transcripts(question)
    if snippet:
        # Pedir ao GPT que reescreva e ensine
        prompt = (
            f"Você é Nanda Mac.ia, professora didática. Reescreva o seguinte trecho do curso em suas próprias palavras, "
            f"como se estivesse explicando em aula, resumindo os pontos principais, adicionando exemplos práticos "
            f"e fazendo uma pergunta de acompanhamento ao aluno.\n\n"  
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
