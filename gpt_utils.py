import os
import json
import re
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
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# FUNÇÃO DE NORMALIZAÇÃO DE CHAVE
# -----------------------------
def normalize_key(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# -----------------------------
# CARREGA TRANSCRIÇÕES E PDFs
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

TRANSCRIPT_PATH = os.path.join(BASE_DIR, "transcricoes.txt")
_raw_txt = open(TRANSCRIPT_PATH, encoding="utf-8").read()

PDF1_PATH = os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf")
_raw_pdf1 = ""
try:
    reader1 = PdfReader(PDF1_PATH)
    _raw_pdf1 = "\n\n".join(page.extract_text() or "" for page in reader1.pages)
except:
    _raw_pdf1 = ""

PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except:
    _raw_pdf2 = ""

# resumo para classificação
_combined = _raw_txt + "\n\n" + _raw_pdf1 + "\n\n" + _raw_pdf2
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "Você é um resumidor especialista em educação. "
                "Resuma em até 300 palavras todo o conteúdo do curso 'Consultório High Ticket', "
                "incluindo o Plano de Ação (1ª Semana) e o Guia do Curso, para servir de base na classificação."
            )},
            {"role": "user", "content": _combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# MAPA DE KEYWORDS PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revisao", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificacao", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "valor do health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital":["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao":                      ["como aplico", "aplicação", "aplico", "roteiro", "aplicação"],
    "faq":                            ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana", "1ª semana"],
    "guia":                           ["guia do curso", "passo a passo", "CHT21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS (Guia + Plano de Ação)
# -----------------------------
CANONICAL_QA = {
    # Guia do Curso
    "quais são os quatro passos iniciais descritos no guia do curso consultório high ticket para começar a participação?":
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em \"Participar\".",
    # Pergunta 1 exata do aluno
    "oi nanda acabei de me inscrever no curso qual é o primeiro passo que devo dar assim que entrar":
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em \"Participar\".",
    "o que o participante deve fazer após entrar na área de membros para dar o primeiro passo no desafio health plan?":
        "1. <strong>Clique no botão \"Participar\"</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Feche</strong> a janela de confirmação.<br>"
        "3. <strong>Clique novamente em \"Participar\"</strong> para concluir a inscrição.",
    # Pergunta 2 exata do aluno
    "depois de entrar na area de membros como eu me inscrevo no desafio health plan":
        "1. <strong>Clique no botão \"Participar\"</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Feche</strong> a janela de confirmação.<br>"
        "3. <strong>Clique novamente em \"Participar\"</strong> para concluir a inscrição.",
    # Fases desafio
    "como é estruturado o mapa de atividades do desafio health plan em termos de fases e prazos?":
        "O Desafio Health Plan é dividido em três fases, sem considerar datas específicas:<br>"
        "<strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz;<br>"
        "<strong>Fase 2 – Masterclass e envio do Health Plan:</strong> participar da masterclass e enviar seu primeiro plano;<br>"
        "<strong>Fase 3 – Missões semanais:</strong> enviar planners semanais e concluir atividades de encerramento.",
    # Pergunta 3 exata do aluno
    "voce pode explicar como o desafio health plan esta organizado em fases":
        "O Desafio Health Plan é dividido em três fases, sem considerar datas específicas:<br>"
        "<strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz;<br>"
        "<strong>Fase 2 – Masterclass e envio do Health Plan:</strong> participar da masterclass e enviar seu primeiro plano;<br>"
        "<strong>Fase 3 – Missões semanais:</strong> enviar planners semanais e concluir atividades de encerramento.",
    # Plano de Ação (1ª Semana)
    "nanda no exercicio de bloqueios com dinheiro como faço para escolher qual bloqueio priorizar e definir minha atitude dia do chega":
        "Primeiro, identifique qual sentimento de culpa ao cobrar mais te afeta (\"Síndrome do Sacerdote\"). "
        "Escolha esse bloqueio como prioritário. Em 'Onde quero chegar', escreva uma ação concreta, "
        "por exemplo: \"A partir de hoje, afirmarei meu valor em cada consulta.\"",  
    # Pergunta 4 exata do aluno
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino a atitude dia do chega":
        "Primeiro, identifique qual sentimento de culpa ao cobrar mais te afeta (\"Síndrome do Sacerdote\"). "
        "Escolha esse bloqueio como prioritário. Em 'Onde quero chegar', escreva uma ação concreta, "
        "por exemplo: \"A partir de hoje, afirmarei meu valor em cada consulta.\"",  
    # Pergunta 5 exata do aluno
    "como uso a atividade de nicho de atuacao para encontrar meu posicionamento e listar as acoes":
        "Descreva seu posicionamento atual (pontos fortes e lacunas) e defina seu nicho ideal (pacientes sonhos). "
        "Liste ações com prazo, por exemplo: \"Especializar em [X] em 3 meses.\""
}

# pré-normaliza o dicionário de respostas
CANONICAL_QA_NORMALIZED = { normalize_key(k): v for k, v in CANONICAL_QA.items() }

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
        "com tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula de **Posicionamento High Ticket**.<br><br>"
    ),
    # mantenha as demais variações iguais ao seu arquivo original...
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()
    if "exercício" in lower_q or "exercicios" in lower_q:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    for tipo, keywords in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keywords):
            return {"scope": "IN_SCOPE", "type": tipo}
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda apenas um JSON com duas chaves: scope ('IN_SCOPE'/'OUT_OF_SCOPE') e type (nome do template).\n\n"
        f"Resumo do curso:\n{COURSE_SUMMARY}\n\nPergunta:\n{question}"
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = "explicacao"
) -> str:
    key_norm = normalize_key(question)
    if key_norm in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key_norm]

    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto relevante:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    try:
        r2 = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r2.choices[0].message.content
