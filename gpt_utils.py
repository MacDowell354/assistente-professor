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
# NORMALIZAÇÃO DE CHAVE (removendo acentos)
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    clean = no_accents.lower()
    clean = re.sub(r"[^\w\s]", "", clean)
    return re.sub(r"\s+", " ", clean).strip()

# -----------------------------
# LEITURA DE ARQUIVOS PDF
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

# combinado apenas para classificação via LLM
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso e Dossiê 007."
            },
            {"role":"user","content":_combined}
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
    "dossie":                         ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"],
    "canva_health_plan":              ["modelo compartilhado do health plan", "link do health plan"],
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
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em ‘Participar’.",
    "depois de entrar na area de membros como eu me inscrevo no desafio health plan":
        "1. <strong>Clique em ‘Participar’</strong> no módulo Desafio Health Plan.<br>"
        "2. Feche a janela de confirmação.<br>"
        "3. Clique novamente em <strong>‘Participar’</strong> para efetivar.<br>"
        "4. Feche e você estará inscrito.",
    "voce pode explicar como o desafio health plan esta organizado em fases":
        "O Desafio Health Plan possui três fases (sem datas fixas):<br>"
        "- <strong>Fase 1 – Missão inicial:</strong> assistir módulos 1–6 e preencher quiz.<br>"
        "- <strong>Fase 2 – Masterclass & Envio:</strong> participar da masterclass e enviar seu plano.<br>"
        "- <strong>Fase 3 – Acompanhamento:</strong> enviar planners semanais e concluir atividades.",
    "caso o participante enfrente uma situacao critica qual procedimento deve ser adotado para solicitar suporte":
        "Em caso crítico, envie e-mail para <strong>ajuda@nandamac.com</strong> com assunto <strong>S.O.S Crise</strong>. A equipe retornará em até 24 h.",
    "onde e como o participante deve tirar duvidas sobre o metodo do curso":
        "Poste dúvidas exclusivamente na <strong>Comunidade</strong> da Área de Membros. Não use Direct, WhatsApp ou outros canais.",

    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino minha atitude dia do chega":
        "Identifique o bloqueio de culpa que mais afeta (Síndrome do Sacerdote) como prioritário. "
        "Em “Onde quero chegar”, escreva: “A partir de hoje, afirmarei meu valor em cada consulta e não deixarei de cobrar pelo meu trabalho.”",
    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar certas situacoes me abalar":
        "Liste duas situações que abalaram sua confiança. "
        "Em “Onde quero chegar”, defina: “Sempre que receber críticas, realizarei uma sessão de feedback construtivo com um colega.”",
    "como uso a atividade de nicho de atuacao para definir meu foco e listar as acoes necessarias":
        "Descreva seu posicionamento atual e identifique seu nicho ideal. Liste ações específicas com prazo, como “Especializar em [X] em 3 meses”.",
    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais":
        "Anote seus valores atuais; pesquise referências de mercado; considere custos, experiência e diferenciais; defina valores ideais, ex.: “R$ 300 por sessão, com relatório personalizado.”",
    "ainda nao tenho pacientes particulares qual estrategia de atracao de pacientes high ticket devo priorizar e como executar na agenda":
        "Reserve um bloco fixo (ex.: segundas 8h–10h) para enviar 5 mensagens personalizadas ao seu nicho. Depois, implemente a Patient Letter com convites impressos.",

    # — Dossiê 007 —
    "qual e o objetivo principal do dossie 007 e para quem ele e indicado":
        "O Dossiê 007 ensina as estratégias iniciais do Método Consultório High Ticket para atrair e reter Pacientes High Ticket. É indicado para profissionais sem pacientes, quem atende convênios e quem já atende particulares e quer dobrar faturamento.",
    "como implementar a acao 1 de networking descrita no dossie 007":
        "Identifique outros profissionais que atendem seus pacientes e envie um áudio de até 40s: 'Oi |Nome|, aqui é o Dr. |Seu Nome|. Podemos conversar 10 minutos sobre o paciente X? Horário: Xh ou Yh?' ",
    "quais scripts devo usar para confirmar e remarcar consultas na acao 2 do dossie 007":
        "• Confirmação (2 dias antes): “Oi [nome], confirmo sua consulta dia X às Y h. Digite 1 para confirmar, 2 para cancelar.”<br>"
        "• Remarcação (1 h antes): “A agenda está concorrida; próximo horário disponível em X meses. Tem certeza de remarcar?”",
    "como funciona a acao 3 de reativacao high ticket e qual script usar para pacientes antigos":
        "Após 6 meses sem visita, envie: “Oi [nome], sou assistente da Dra X, faz X meses desde sua última consulta. Vamos agendar?” Se não responder em 48 h, envie: “Seu feedback é importante. Algo mudou?”",
    "quais sao as orientacoes finais do dossie 007 e como aplica-las":
        "1. Destaque sua especialidade específica;<br>2. Tudo é sobre o paciente;<br>3. Ligue e agradeça pessoalmente aos profissionais que recomendaram pacientes.",

    # — Health Plan Compartilhado (Canva) —
    "onde posso acessar o modelo compartilhado do health plan":
        "Acesse o modelo de Health Plan nas aulas 6.8 e 10.4 via Canva: "
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">Modelo Health Plan (Canva)</a>. :contentReference[oaicite:1]{index=1}",
    "em qual aula e apresentado o link do health plan compartilhado":
        "O link do Health Plan compartilhado aparece na Aula 6.8 e na Aula 10.4. :contentReference[oaicite:2]{index=2}",
    "para que serve o link do health plan compartilhado":
        "Esse link oferece um modelo editável no Canva para você personalizar e apresentar o Health Plan aos pacientes. :contentReference[oaicite:3]{index=3}",
    "como editar o health plan no canva":
        "Abra o link, clique em “Editar este modelo” (login no Canva requerido) e altere textos, imagens e cores conforme sua marca. :contentReference[oaicite:4]{index=4}",
    "posso compartilhar o health plan com meus pacientes":
        "Após editar, clique em “Compartilhar” e copie o link de visualização para enviar a seus pacientes. :contentReference[oaicite:5]{index=5}",
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
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente,<br>ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "faq": (
        "<strong>Objetivo:</strong> Responder de forma direta a dúvidas frequentes do curso. "
        "Use exemplos práticos e links ativos conforme o material."
    ),
    # demais variações mantidas...
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in key for k in kws):
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
    key = normalize_key(question)
    # 1) Resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Classificação de escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Monta prompt dinâmico
    prompt = identidade + prompt_variacoes.get(cls["type"], "")
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
