import os
import json
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
# MENSAGEM PADRÃO PARA FORA DE ESCOPO
# -----------------------------
OUT_OF_SCOPE_MSG = (
    "Essa pergunta é muito boa, mas no momento ela está "
    "<strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma "
    "oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar "
    "a inclusão em versões futuras do curso. Enquanto isso, "
    "recomendamos focar nos ensinamentos já disponíveis para ter "
    "os melhores resultados possíveis no consultório."
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
# LEITURA DOS ARQUIVOS
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def read_pdf(path):
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

_raw_txt  = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "5.8 - Dossiê 007 - (3)[1].pdf"))

_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso e Dossiê 007."},
            {"role": "user", "content": _combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# PALAVRAS-CHAVE PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital":["offline", "sem instagram", "sem anúncios"],
    "aplicacao":                      ["como aplico", "aplicação", "roteiro"],
    "faq":                            ["quais", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "dossie":                         ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # Guia do Curso
    "oi nanda acabei de me inscrever no curso qual e o primeiro passo que devo dar assim que entrar":
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>2. <strong>Passo 2:</strong> Entre no grupo de avisos da turma.<br>3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em “Participar”.",
    "depois de entrar na area de membros como eu me inscrevo no desafio health plan":
        "1. <strong>Clique em “Participar”</strong> no módulo Desafio Health Plan.<br>2. Feche a janela de confirmação.<br>3. Clique novamente em <strong>“Participar”</strong> para efetivar.<br>4. Feche e você estará inscrito.",
    "voce pode explicar como o desafio health plan esta organizado em fases":
        "O Desafio Health Plan possui três fases (sem datas fixas):<br>- <strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz.<br>- <strong>Fase 2 – Masterclass & Envio:</strong> participar da masterclass e enviar seu plano.<br>- <strong>Fase 3 – Acompanhamento:</strong> enviar planners semanais e concluir atividades.",
    "caso o participante enfrente uma situacao critica qual procedimento deve ser adotado para solicitar suporte":
        "Em caso crítico, envie e-mail para <strong>ajuda@nandamac.com</strong> com assunto <strong>S.O.S Crise</strong>. A equipe retornará em até 24 h.",
    "onde e como o participante deve tirar duvidas sobre o metodo do curso":
        "Poste dúvidas exclusivamente na <strong>Comunidade</strong> da Área de Membros. Não use Direct, WhatsApp ou outros canais.",
    "como entro na comunidade high ticket":
        "A Comunidade High Ticket Doctors está dentro da plataforma do curso. Assim que você receber o e-mail com o título “Chegou seu acesso”, cadastre sua senha. Depois de logado, preencha seu perfil e entre na Comunidade para tirar dúvidas sobre o método, fazer networking e participar das oficinas.",

    # Pergunta nova adicionada
    "quais sao as principais duvidas que alunos normalmente tem sobre captacao de pacientes sem usar redes sociais":
        "Ótima pergunta! No curso, muitos alunos relatam dúvidas sobre como atrair pacientes sem depender do Instagram, anúncios ou tráfego pago. A Nanda ensina diversas estratégias offline, como indicações qualificadas, cartas de paciente, networking com outros profissionais da saúde e scripts personalizados. Você pode começar organizando um roteiro de Patient Letter e distribuindo para pacientes estratégicos.",

    # Plano de Ação e Dossiê mantidos (mesmo conteúdo original)
    # ...
}

CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. "
        "Use uma linguagem clara e didática, com tópicos ou passos. Evite genéricos.<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder de forma direta a dúvidas frequentes do curso. "
        "Use exemplos práticos e mencione etapas conforme o material."
    ),
    # demais variações seguem conforme o projeto
}

# -----------------------------
# CLASSIFICADOR
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if lower in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(question: str, context: str = "", history: str = None, tipo_de_prompt: str = None) -> str:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.
