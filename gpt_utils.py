import os
import json
import unicodedata
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
# FUNÇÃO DE NORMALIZAÇÃO
# -----------------------------
def normalize(text: str) -> str:
    # retira acentos, pontuação e deixa tudo em minúsculas
    txt = unicodedata.normalize('NFD', text)
    txt = ''.join(ch for ch in txt if unicodedata.category(ch) != 'Mn')
    txt = re.sub(r'[^a-z0-9\s]', '', txt)
    return txt.lower().strip()

# -----------------------------
# CARREGA TRANSCRIÇÕES E PDFs (1× NO STARTUP)
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

# 1) texto das transcrições
TRANSCRIPT_PATH = os.path.join(BASE_DIR, "transcricoes.txt")
_raw_txt = open(TRANSCRIPT_PATH, encoding="utf-8").read()

# 2) texto do Plano de Ação (1ª Semana)
PDF1_PATH = os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf")
_raw_pdf1 = ""
try:
    reader1 = PdfReader(PDF1_PATH)
    _raw_pdf1 = "\n\n".join(page.extract_text() or "" for page in reader1.pages)
except:
    _raw_pdf1 = ""

# 3) texto do Guia do Curso
PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except:
    _raw_pdf2 = ""

# Combina tudo para resumo (usado apenas na classificação via GPT)
_combined = _raw_txt + "\n\n" + _raw_pdf1 + "\n\n" + _raw_pdf2
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um resumidor especialista em educação. "
                    "Resuma em até 300 palavras todo o conteúdo do curso “Consultório High Ticket”, "
                    "incluindo o plano de ação da primeira semana e o Guia do Curso, "
                    "para servir de base na classificação de escopo e tipo de prompt."
                )
            },
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
    "guia":                           ["guia do curso", "passo a passo", "cht21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS (Guia + Plano de Ação)
# -----------------------------
CANONICAL_QA = {
    # — Guia do Curso —
    "oi nanda acabei de me inscrever no curso qual e o primeiro passo que devo dar assim que entrar": (
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em “Participar”."
    ),
    "depois de entrar na area de membros como eu me inscrevo no desafio health plan": (
        "1. <strong>Clique em “Participar”</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Fechar</strong> a janela inicial.<br>"
        "3. Na próxima tela, <strong>clique novamente em “Participar”</strong> para efetivar a inscrição.<br>"
        "4. Clique em <strong>Fechar</strong> para concluir."
    ),
    "voce pode explicar como o desafio health plan esta organizado em fases": (
        "O Desafio Health Plan é dividido em três fases, **sem datas fixas**:\n"
        "- **Fase 1 – Missão inicial:** Assistir aos módulos 1–6 e preencher o quiz.\n"
        "- **Fase 2 – Masterclass & Envio:** Participar da Masterclass de Health Plan e enviar seu primeiro plano.\n"
        "- **Fase 3 – Acompanhamento:** Realizar envios semanais de planners de consecutividade e atividades de encerramento."
    ),
    "caso o participante enfrente uma situacao critica qual procedimento deve ser adotado para solicitar suporte": (
        "Em caso de situação crítica, envie um e-mail para <strong>ajuda@nandamac.com</strong> "
        "com o assunto <strong>S.O.S Crise</strong>. A equipe retornará em até 24 horas."
    ),
    "onde e como o participante deve tirar duvidas sobre o metodo do curso": (
        "Poste suas dúvidas exclusivamente na <strong>Comunidade</strong> da Área de Membros. "
        "Não utilize Direct, WhatsApp ou outros canais para dúvidas sobre o método."
    ),
    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino a atitude dia do chega": (
        "Dos bloqueios identificados, escolha aquele que mais gera culpa (“Síndrome do Sacerdote”) como prioritário. "
        "Em “Onde quero chegar”, defina uma atitude concreta para o Dia do Chega, ex.: “A partir de hoje, afirmarei meu valor em cada consulta.”"
    ),
    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar mais certas situacoes me abalar": (
        "Liste duas experiências que abalaram sua confiança. Em “Onde quero chegar”, defina uma atitude transformadora, ex.: "
        "“Sempre que receber uma crítica, farei uma sessão de feedback construtivo com um colega.”"
    ),
    "como uso a atividade de nicho de atuacao para encontrar meu posicionamento e listar as acoes": (
        "Descreva seu posicionamento atual (forças e lacunas) e defina seu nicho ideal. "
        "Liste ações específicas, com prazos, ex.: “Fazer especialização em [X] em 3 meses.”"
    ),
    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais": (
        "Anote seus preços atuais, pesquise tabelas de associações ou colegas para médias de mercado e defina valores ideais, justificando seu diferencial, ex.: “R$ 300 por sessão de fisioterapia clínica.”"
    ),
    "ainda nao tenho pacientes particulares qual estrategia de atracao de pacientes high ticket devo priorizar e como executar na agenda": (
        "Reserve um bloco fixo na agenda (ex.: toda segunda 8h–10h) para enviar 5 mensagens personalizadas ao Mercado X usando o script do curso. "
        "Quando iniciar atendimentos, implemente a Patient Letter com convites impressos para potenciais pacientes High Ticket."
    )
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize(question)
    if "exercicio" in lower and "bloqueios" in lower:
        # mas se for um dos canônicos, ele vai bater antes
        return {"scope": "IN_SCOPE", "type": "plano_de_acao"}
    for tipo, kws in TYPE_KEYWORDS.items():
        if any(normalize(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": tipo}
    # fallback:
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar o método na prática.<br><br>"
)
prompt_variacoes = {
    # ... (seus outros templates aqui)
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. "
        "Use linguagem clara e tópicos. Evite genéricos.<br><br>"
    ),
}

# -----------------------------
# GERAÇÃO DA RESPOSTA
# -----------------------------
def generate_answer(question: str, context: str = "", history: str = None) -> str:
    key = normalize(question)
    if key in CANONICAL_QA:
        return CANONICAL_QA[key]

    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # se não é canônica, chamamos o GPT normal
    prompt = identidade + prompt_variacoes.get(cls["type"], "") 
    if context:
        prompt += f"<br><br><strong>📚 Contexto:</strong><br>{context}<br>"
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
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
    return r.choices[0].message.content
