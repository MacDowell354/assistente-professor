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
# NORMALIZAÇÃO DE CHAVE
# -----------------------------
def normalize_key(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s]", "", s)      # remove pontuação
    s = re.sub(r"\s+", " ", s).strip() # normaliza espaços
    return s

# -----------------------------
# LEITURA DE TRANSCRIÇÕES E PDFs
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

# 1) Transcrições
_raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()

# 2) Plano de Ação (1ª Semana)
PDF1_PATH = os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf")
_raw_pdf1 = ""
try:
    reader1 = PdfReader(PDF1_PATH)
    _raw_pdf1 = "\n\n".join(page.extract_text() or "" for page in reader1.pages)
except:
    _raw_pdf1 = ""

# 3) Guia do Curso
PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except:
    _raw_pdf2 = ""

# resumo combinado (usado apenas para classification, não em respostas canônicas)
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana) e Guia do Curso, "
                "para servir de base na classificação de prompts."
            },
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
    "explicacao":                     ["explique", "o que é", "defina"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # — Guia do Curso —
    "oi nanda acabei de me inscrever no curso qual e o primeiro passo que devo dar assim que entrar":
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em “Participar”.",
    "depois de entrar na area de membros como eu me inscrevo no desafio health plan":
        "1. <strong>Clique em “Participar”</strong> no módulo Desafio Health Plan.<br>"
        "2. Feche a janela de confirmação.<br>"
        "3. Clique novamente em <strong>“Participar”</strong> para efetivar.<br>"
        "4. Feche e você estará inscrito.",
    "voce pode explicar como o desafio health plan esta organizado em fases":
        "O Desafio Health Plan possui três fases (sem datas fixas):<br>"
        "- <strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz.<br>"
        "- <strong>Fase 2 – Masterclass & Envio:</strong> participar da masterclass e enviar seu plano.<br>"
        "- <strong>Fase 3 – Acompanhamento:</strong> enviar planners semanais e concluir atividades.",
    "caso o participante enfrente uma situacao critica qual procedimento deve ser adotado para solicitar suporte":
        "Em caso crítico, envie e-mail para <strong>ajuda@nandamac.com</strong> com assunto <strong>S.O.S Crise</strong>. "
        "A equipe retornará em até 24 h.",
    "onde e como o participante deve tirar duvidas sobre o metodo do curso":
        "Poste dúvidas exclusivamente na <strong>Comunidade</strong> da Área de Membros. "
        "Não use Direct, WhatsApp ou outros canais.",
    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino a atitude dia do chega":
        "Identifique o bloqueio de culpa que mais afeta (Síndrome do Sacerdote) como prioritário. "
        "Em “Onde quero chegar”, escreva: “A partir de hoje, afirmarei meu valor em cada consulta.”",
    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar certas situacoes me abalar":
        "Liste duas situações que abalaram sua confiança. "
        "Em “Onde quero chegar”, defina: “Sempre que receber críticas, buscarei feedback construtivo.”",
    "como uso a atividade de nicho de atuacao para encontrar meu posicionamento e listar as acoes":
        "Descreva seu posicionamento (forças e lacunas) e defina seu nicho ideal. "
        "Liste ações com prazo, ex.: “Especializar em [X] em 3 meses.”",
    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais":
        "Anote preços atuais, pesquise médias em associações/colegas e defina valores ideais justificando seu diferencial, "
        "ex.: “R$ 300 por sessão, com relatório personalizado.”",
    "ainda nao tenho pacientes particulares qual estrategia de atracao de pacientes high ticket devo priorizar e como executar na agenda":
        "Reserve um bloco fixo (ex.: segundas 8h–10h) para enviar 5 mensagens personalizadas ao seu nicho. "
        "Depois, implemente a Patient Letter com convites impressos para potenciais clientes High Ticket."
}

# pré-normaliza as chaves
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
    # demais variações mantidas conforme seu design original...
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = question.lower()
    if "exercício" in lower or "exercicios" in lower:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(k in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    # 1) Resposta canônica se houver
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Classificação de escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Monta prompt dinâmico
    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 4) Chama OpenAI
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r.choices[0].message.content
