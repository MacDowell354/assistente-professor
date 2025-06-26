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
except Exception:
    _raw_pdf1 = ""

# 3) texto do Guia do Curso
PDF2_PATH = os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf")
_raw_pdf2 = ""
try:
    reader2 = PdfReader(PDF2_PATH)
    _raw_pdf2 = "\n\n".join(page.extract_text() or "" for page in reader2.pages)
except Exception:
    _raw_pdf2 = ""

# Combina tudo para resumo
_combined = _raw_txt + "\n\n" + _raw_pdf1 + "\n\n" + _raw_pdf2

# Pede resumo ao GPT-4
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
# MAPA DE KEYWORDS PARA TIPO DE PROMPT
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
# RESPOSTAS CANÔNICAS PARA 5 PERGUNTAS DO GUIA + SINÔNIMOS DE CRISE
# -----------------------------
CANONICAL_QA = {
    # 1. Quatro passos iniciais
    "quais são os quatro passos iniciais descritos no guia do curso consultório high ticket para começar a participação?": (
        "1. <strong>Passo 1:</strong> Assista à aula de Onboarding completo.<br>"
        "2. <strong>Passo 2:</strong> Entre no grupo exclusivo de avisos da turma.<br>"
        "3. <strong>Passo 3:</strong> Acesse a Área de Membros e preencha seu perfil.<br>"
        "4. <strong>Passo 4:</strong> Participe do Desafio Health Plan clicando em “Participar”."
    ),
    # 2. Inscrição no Desafio
    "o que o participante deve fazer após entrar na área de membros para dar o primeiro passo no desafio health plan?": (
        "1. <strong>Clicar em “Participar”</strong> no módulo Desafio Health Plan.<br>"
        "2. <strong>Fechar</strong> a janela inicial.<br>"
        "3. Na tela seguinte, <strong>clicar novamente em “Participar”</strong> para efetivar sua inscrição no desafio."
    ),
    # 3. Mapa de atividades sem datas
    "como é estruturado o mapa de atividades do desafio health plan em termos de fases e prazos?": (
        "O mapa de atividades do Desafio Health Plan é dividido em três fases, sem considerar datas específicas:<br>"
        "<strong>Fase 1 – Missão inicial:</strong> assistir aos módulos 1–6 e preencher o quiz correspondente;<br>"
        "<strong>Fase 2 – Masterclass e envio do Health Plan:</strong> participar da masterclass de Health Plan e enviar o primeiro plano produzido;<br>"
        "<strong>Fase 3 – Missões semanais de acompanhamento:</strong> realizar envios semanais de planners de consecutividade e participar das atividades de encerramento."
    ),
    # 4. Suporte em caso de urgência/crise
    "caso o participante enfrente uma situação crítica, qual procedimento deve ser adotado para solicitar suporte?": (
        "Em caso de situação crítica, envie um e-mail para <strong>ajuda@nandamac.com</strong> com o assunto <strong>“S.O.S Crise”</strong>. "
        "A equipe de suporte retornará em até 24 horas."
    ),
    # 5. Dúvidas sobre o método
    "onde e como o participante deve tirar dúvidas sobre o método do curso?": (
        "As dúvidas sobre o método devem ser postadas exclusivamente na <strong>Comunidade</strong> da Área de Membros. "
        "Não utilize Direct, WhatsApp ou outros canais para questionamentos metodológicos."
    )
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()
    # bloquear exercícios físicos
    if "exercício" in lower_q or "exercicios" in lower_q:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}
    # 1) match rápido por keyword
    for tipo, keywords in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in keywords):
            return {"scope": "IN_SCOPE", "type": tipo}
    # 2) fallback via GPT
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda **apenas** um JSON com duas chaves:\\n"
        "  • scope: 'IN_SCOPE' ou 'OUT_OF_SCOPE'\\n"
        "  • type: nome de um template (ex: 'explicacao', 'health_plan', 'plano_de_acao', 'guia', etc)\\n\\n"
        f"Resumo do curso:\\n{COURSE_SUMMARY}\\n\\n"
        f"Pergunta:\\n{question}\\n\\n"
        "Exemplo de resposta válida:\\n"
        '{ \"scope\": \"IN_SCOPE\", \"type\": \"guia\" }'
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": payload}]
        )
        return json.loads(r.choices[0].message.content)
    except (OpenAIError, json.JSONDecodeError):
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

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
    "faq": (
        "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
        "Use exemplos práticos e aplique o método passo a passo."
    ),
    "revisao": (
        "<strong>Objetivo:</strong> Fazer uma revisão rápida dos pontos centrais do método de precificação estratégica. "
        "Use exatamente seis bullets, cada um iniciando com verbo de ação e título em negrito: "
        "**Identificar Pacientes Potenciais**, **Determi...
