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
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso "
    "Consultório High Ticket</strong>. Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
)

# -----------------------------
# NORMALIZAÇÃO DE CHAVE (removendo acentos)
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize('NFD', text)
    ascii_only = ''.join(ch for ch in nfkd if unicodedata.category(ch) != 'Mn')
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# LEITURA DE TRANSCRIÇÕES E PDFs
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

_raw_txt = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()

def read_pdf(path):
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "Papelaria e brindes  lista de links e indicações.pdf"))

# combinado apenas para classificação via LLM
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso e o material de Papelaria e Brindes."
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
    "faq":                            ["quais", "pergunta frequente", "duvidas", "dúvidas"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  [
        "plano de ação", "primeira semana",
        "bloqueios com dinheiro", "autoconfianca profissional",
        "nicho de atuacao", "valor da consulta",
        "ainda nao tenho pacientes particulares"
    ],
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
        "- **Fase 1 – Missão inicial:** assistir módulos 1–6 e preencher quiz.<br>"
        "- **Fase 2 – Masterclass & Envio:** participar da masterclass e enviar seu plano.<br>"
        "- **Fase 3 – Acompanhamento:** enviar planners semanais e concluir atividades.",
    "como esta dividido o mapa de atividades do desafio health plan em fases":
        "O Desafio Health Plan possui três fases (sem datas fixas):<br>"
        "- **Fase 1 – Missão inicial:** assistir módulos 1–6 e preencher quiz.<br>"
        "- **Fase 2 – Masterclass & Envio:** participar da masterclass e enviar seu plano.<br>"
        "- **Fase 3 – Acompanhamento:** enviar planners semanais e concluir atividades.",
    "caso o participante enfrente uma situacao critica qual procedimento deve ser adotado para solicitar suporte":
        "Em caso crítico, envie e-mail para **ajuda@nandamac.com** com assunto **S.O.S Crise**. A equipe retornará em até 24h.",
    "onde e como o participante deve tirar duvidas sobre o metodo do curso":
        "Poste dúvidas exclusivamente na **Comunidade** da Área de Membros. Não use Direct, WhatsApp ou outros canais.",
    "onde devo postar minhas duvidas sobre o metodo do curso":
        "Todas as dúvidas sobre o método devem ser postadas **exclusivamente na Comunidade** da Área de Membros.",

    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino minha atitude dia do chega":
        "Identifique o bloqueio de culpa que mais afeta (Síndrome do Sacerdote) como prioritário. Em “Onde quero chegar”, escreva: “A partir de hoje, afirmarei meu valor em cada consulta e não deixarei de cobrar pelo meu trabalho.”",
    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar certas situacoes me abalar":
        "Liste duas situações que abalaram sua confiança. Em “Onde quero chegar”, defina uma atitude transformadora, por exemplo: “Sempre que receber uma crítica, realizarei uma sessão de feedback construtivo com um colega.”",
    "como uso a atividade de nicho de atuacao para definir meu foco e listar as acoes necessarias":
        "Descreva seu posicionamento atual e identifique seu nicho ideal. Em seguida, liste ações específicas com prazo, por exemplo: “Especializar em [X] em 3 meses”, “Criar pacote online de avaliação inicial até o próximo mês” e “Revisar site e materiais de comunicação em 2 semanas.”",
    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais":
        "Anote seus valores atuais para consulta e procedimentos; pesquise referências de mercado em tabelas de associações ou colegas; considere custos, experiência e diferenciais; e defina seus valores ideais justificando seu diferencial, por exemplo: “R$ 300 por sessão de fisioterapia clínica, incluindo relatório personalizado de evolução.”",
    "ainda nao tenho pacientes particulares qual estrategia de atracao high ticket devo priorizar e como executar na agenda":
        "Reserve um bloco fixo na agenda (por exemplo, toda segunda, das 8h às 10h) para enviar 5 mensagens personalizadas a potenciais pacientes do seu nicho usando o roteiro do curso. Quando iniciar atendimentos, implemente a Patient Letter enviando convites impressos aos pacientes para estimular indicações de alto valor.",

    # — Papelaria & Brindes —
    "onde encontro produtos jo malone no brasil":
        "Você pode encontrar aromas de ambiente Jo Malone no Brasil em https://www.jomalone.com.br, incluindo colônias Blackberry & Bay, Wood Sage & Sea Salt, Lime Basil & Mandarin e Nectarine Blossom & Honey. :contentReference[oaicite:5]{index=5}",
    "quais importadoras posso usar para produtos nao encontrados no brasil":
        "Para produtos não encontrados no Brasil, use importadoras como Easy to go Orlando (https://easytogoorlando.com/) ou marketplaces internacionais como Amazon. :contentReference[oaicite:6]{index=6}",
    "quais marcas de cafeteiras foram mencionadas":
        "As marcas de cafeteiras recomendadas incluem Delonghi, Nespresso e Breville. :contentReference[oaicite:7]{index=7}",
    "onde posso comprar chocolates mencionados no curso":
        "Os chocolates indicados são Laderach e Daim, disponíveis em chocolaterias especializadas e lojas online. :contentReference[oaicite:8]{index=8}",
    "quais opcoes de chas foram indicadas":
        "As opções de chás recomendadas são New English Teas Vintage Victorian Round Tea Caddy e Twinings Earl Grey Loose Tea Tins. :contentReference[oaicite:9]{index=9}"
}

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
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use linguagem clara e tópicos. Evite genéricos.<br><br>"
    ),
    # demais variações mantidas...
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
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
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    # 1) se canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]
    # 2) escopo/tipo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG
    # 3) prompt dinâmico
    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"
    # 4) chamada OpenAI
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role":"user","content":prompt}]
        )
    except OpenAIError:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
    return r.choices[0].message.content
