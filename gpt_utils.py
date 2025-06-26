import os
import json
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

_combined = _raw_txt + "\n\n" + _raw_pdf1 + "\n\n" + _raw_pdf2

try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "Você é um resumidor especialista em educação. "
                "Resuma em até 300 palavras todo o conteúdo do curso ‘Consultório High Ticket’, "
                "incluindo o plano de ação da primeira semana e o Guia do Curso, "
                "para servir de base na classificação de escopo e tipo de prompt."
            )},
            {"role": "user", "content": _combined}
        ]
    )
    COURSE_SUMMARY = resp.choices[0].message.content
except OpenAIError:
    COURSE_SUMMARY = ""

# -----------------------------
# KEYWORDS PARA TIPO DE PROMPT
# -----------------------------
TYPE_KEYWORDS = {
    "revisao": ["revisão", "revisao", "revise", "resumir"],
    "precificacao": ["precificação", "precificacao", "precificar", "preço", "valor", "faturamento"],
    "health_plan": ["health plan", "valor do health plan", "retorno do investimento"],
    "capitacao_sem_marketing_digital": ["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao": ["como aplico", "aplicação", "aplico", "roteiro", "aplicação"],
    "faq": ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao": ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao": ["plano de ação", "primeira semana", "1ª semana"],
    "guia": ["guia do curso", "passo a passo", "CHT21"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS (GUIDA + PLANO DE AÇÃO)
# -----------------------------
CANONICAL_QA = {
    # Guia do Curso
    "quais são os quatro passos iniciais descritos no guia do curso consultório high ticket para começar a participação?": (
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em “Participar”."
    ),
    "o que o participante deve fazer após entrar na área de membros para dar o primeiro passo no desafio health plan?": (
        "1. <strong>Clicar em “Participar”</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Fechar</strong> a janela inicial.<br>"
        "3. Na tela seguinte, <strong>clicar novamente em “Participar”</strong> para efetivar sua inscrição no desafio."
    ),
    "como é estruturado o mapa de atividades do desafio health plan em termos de fases e prazos?": (
        "O mapa de atividades do Desafio Health Plan é dividido em três fases, sem considerar datas específicas:<br>"
        "<strong>Fase 1 – Missão inicial:</strong> assistir aos módulos 1–6 e preencher o quiz correspondente;<br>"
        "<strong>Fase 2 – Masterclass e envio do Health Plan:</strong> participar da masterclass de Health Plan e enviar o primeiro plano produzido;<br>"
        "<strong>Fase 3 – Missões semanais de acompanhamento:</strong> realizar envios semanais de planners de consecutividade e participar das atividades de encerramento."
    ),
    "caso o participante enfrente uma situação crítica, qual procedimento deve ser adotado para solicitar suporte?": (
        "Em caso de situação crítica, envie um e-mail para <strong>ajuda@nandamac.com</strong> com o assunto <strong>‘S.O.S Crise’</strong>. "
        "A equipe de suporte retornará em até 24 horas."
    ),
    "onde e como o participante deve tirar dúvidas sobre o método do curso?": (
        "As dúvidas sobre o método devem ser postadas exclusivamente na <strong>Comunidade</strong> da Área de Membros. Não utilize Direct, WhatsApp ou outros canais para questionamentos metodológicos."
    ),
    # Plano de Ação
    "nanda, no exercício de bloqueios com dinheiro, como faço para escolher qual bloqueio priorizar e definir minha atitude ‘dia do chega’?": (
        "Identifique qual sentimento de culpa ao cobrar mais te afeta (\"Síndrome do Sacerdote\"). Escolha esse bloqueio como prioritário. "
        "Em ‘Onde quero chegar’, escreva uma atitude concreta para o Dia do Chega, por exemplo: “A partir de hoje, vou afirmar meu valor em cada consulta.”"
    ),
    "na parte de autoconfiança profissional, o que devo escrever como atitude para não deixar mais certas situações me abalar?": (
        "Liste duas experiências que abalaram sua confiança. Em ‘Onde quero chegar’, defina uma atitude transformadora, por exemplo: “Sempre que receber uma crítica, farei uma sessão de feedback construtivo com um colega.”"
    ),
    "como eu uso a atividade de nicho de atuação para saber se devo mudar meu foco e quais ações listar?": (
        "Descreva seu posicionamento atual (pontos fortes e lacunas) e defina o nicho ideal (pacientes sonhos). "
        "Liste ações específicas com prazos, por exemplo: “Fazer especialização em [X] em 3 meses.”"
    ),
    "no valor da consulta e procedimentos, como encontro referências de mercado e defino meus valores atuais e ideais?": (
        "Anote seus preços atuais, pesquise tabelas de associações ou colegas para médias de mercado, e defina valores ideais justificando seu diferencial, como “R$ 300 por sessão de fisioterapia clínica.”"
    ),
    "ainda não tenho pacientes particulares. qual estratégia de atração de pacientes high ticket devo priorizar e como executar na agenda?": (
        "Reserve um bloco fixo na agenda (ex.: toda segunda das 8h às 10h) para enviar 5 mensagens personalizadas ao Mercado X usando o script do curso. "
        "Quando começar a atender, implemente a Patient Letter com convites impressos para potenciais HT."
    )
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
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, com tópicos ou passos. Evite respostas genéricas."
    ),
    # outras variações...
}

# -----------------------------
# CLASSIFICADOR E GERAÇÃO DE RESPOSTA
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()
    if "exercício" in lower_q or "exercicios" in lower_q:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    for tipo, keywords in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keywords):
            return {"scope": "IN_SCOPE", "type": tipo}
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, responda apenas JSON."
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}


def generate_answer(question: str, context: str = "", history: str = None) -> str:
    key = question.strip().lower()
    if key in CANONICAL_QA:
        return CANONICAL_QA[key]
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG
    prompt = identidade + prompt_variacoes.get(cls["type"], "")
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
