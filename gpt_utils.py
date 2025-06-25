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
    "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado "
    "nas aulas do curso Consultório High Ticket</strong>. Isso pode indicar uma oportunidade "
    "de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras "
    "do curso. Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores "
    "resultados possíveis no consultório."
)

# -----------------------------
# LISTA DE LINKS - MÓDULO 2, AULA 2.5: PAPELARIA E BRINDES
# -----------------------------
LINKS_PAPELARIA_BRINDES = {
    "Easy to Go Orlando": "https://easytogoorlando.com/",
    "Mark & Graham": "https://www.markandgraham.com/",
    "Elo 7": "https://www.elo7.com.br/",
    "Dupla Ideia": "https://duplaideia.com/",
    "Jo Malone - Aromas de Ambiente": "https://www.jomalone.com.br",
    "Privada Eletrônica BidetKing": "https://bidetking.com"
}

# -----------------------------
# CARREGA TRANSCRIÇÕES E PDFs (1× NO STARTUP)
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

# 1) transcrições
txt_path = os.path.join(BASE_DIR, "transcricoes.txt")
with open(txt_path, encoding="utf-8") as f:
    _raw_txt = f.read()

# 2) Plano de Ação (1ª Semana)
_raw_pdf1 = ""
try:
    reader1 = PdfReader(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
    _raw_pdf1 = "\n\n".join(p.extract_text() or "" for p in reader1.pages)
except Exception:
    _raw_pdf1 = ""

# 3) Guia do Curso
_raw_pdf2 = ""
try:
    reader2 = PdfReader(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
    _raw_pdf2 = "\n\n".join(p.extract_text() or "" for p in reader2.pages)
except Exception:
    _raw_pdf2 = ""

# Combina tudo para resumo
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2])

# Pede resumo ao GPT-4
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um resumidor especialista em educação. Resuma em até 300 palavras o conteúdo do curso "
                    ""“Consultório High Ticket”, incluindo o plano de ação da primeira semana e o Guia do Curso, "
                    ""para servir de base na classificação de escopo e tipo de prompt."
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
    "capitacao_sem_marketing_digital": ["offline", "sem usar instagram", "sem instagram", "sem anúncios", "sem anuncios"],
    "aplicacao":                      ["como aplico", "aplicação", "aplico", "roteiro"],
    "faq":                            ["quais", "dúvidas", "duvidas", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana", "1ª semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "papelaria_brindes":              ["papelaria", "brindes", "aula 2.5", "links"]
}

# -----------------------------
# CLASSIFICADOR DE ESCOPO + TIPO
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower_q = question.lower()

    # bloqueia exercícios físicos
    if "exercício" in lower_q or "exercicios" in lower_q:
        return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

    # 1) match rápido por keyword
    for tipo, kws in TYPE_KEYWORDS.items():
        if any(k in lower_q for k in kws):
            return {"scope": "IN_SCOPE", "type": tipo}

    # 2) fallback via GPT
    payload = (
        "Você é um classificador inteligente. Com base no resumo e na pergunta abaixo, "
        "responda **apenas** um JSON com duas chaves:\n"
        "  • scope: 'IN_SCOPE' ou 'OUT_OF_SCOPE'\n"
        "  • type: nome de um template válido\n\n"
        f"Resumo do curso:\n{COURSE_SUMMARY}\n\n"
        f"Pergunta:\n{question}\n\n"
        "Resposta esperada exemplo:\n"
        '{ "scope": "IN_SCOPE", "type": "papelaria_brindes" }'
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
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente, ajudando o aluno a aplicar "
    "o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use linguagem clara e didática, "
        "com passos numerados ou bullets.<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder dúvida frequente. Use exemplos práticos e passo a passo.<br><br>"
    ),
    "revisao": (
        "<strong>Objetivo:</strong> Revisar os pontos centrais do método de precificação estratégica em 6 bullets, "
        "cada um iniciando com verbo de ação e negrito no título, mencionando o benefício de dobrar faturamento e "
        "fidelizar pacientes em ao menos dois bullets.<br><br>"
    ),
    "aplicacao": (
        "<strong>Objetivo:</strong> Aplicar roteiro de atendimento High Ticket na primeira consulta em 6 bullets "
        "com títulos específicos.<br><br>"
    ),
    "capitacao_sem_marketing_digital": (
        "<strong>Objetivo:</strong> Estratégia 100% offline para atrair pacientes de alto valor, passo a passo.<br><br>"
    ),
    "precificacao": (
        "<strong>Objetivo:</strong> Explicar conceito de precificação estratégica. Use bullets com verbo de ação e "
        "destaque Health Plan em inglês.<br><br>"
    ),
    "health_plan": (
        "<strong>Objetivo:</strong> Estruturar apresentação de valor do Health Plan com passos sequenciais e "
        "histórias de sucesso.<br><br>"
    ),
    "plano_de_acao": (
        "<strong>Objetivo:</strong> Auxiliar no Plano de Ação (1ª Semana), cobrindo Bloqueios com dinheiro, "
        "Autoconfiança, Nicho, Valor dos serviços, Convênios vs Particulares, Ambiente do consultório e Ações de atração.<br><br>"
    ),
    "guia": (
        "<strong>Objetivo:</strong> Explorar o Guia do Curso Consultório High Ticket, apresentando passo a passo do PDF "
        "em formato sequencial claro.<br><br>"
    ),
    "papelaria_brindes": (
        "<strong>Objetivo:</strong> Fornecer as indicações de papelaria e brindes da aula 2.5, listando os links recomendados:<br>"
        + "".join(f"➡ <a href=\"{url}\" target=\"_blank\">{name}</a><br>" for name, url in LINKS_PAPELARIA_BRINDES.items())
        + "<br>"
    )
}

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = "explicacao"
) -> str:
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    tipo = cls["type"]
    contexto_para_prompt = "" if tipo == "capitacao_sem_marketing_digital" else (
        f"<br><br><strong>📚 Contexto relevante:</strong><br>{context}<br>" if context.strip() else ""
    )

    prompt = identidad + prompt_variacoes[tipo] + contexto_para_prompt
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
