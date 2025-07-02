import os
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
    "<strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
    "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
    "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
    "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
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
# LEITURA DE ARQUIVOS PDF
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except:
        return ""

# Carrega transcrições e PDFs
_raw_txt  = open(os.path.join(BASE_DIR, "transcricoes.txt"), encoding="utf-8").read()
_raw_pdf1 = read_pdf(os.path.join(BASE_DIR, "PlanodeAcaoConsultorioHighTicket-1Semana (4)[1].pdf"))
_raw_pdf2 = read_pdf(os.path.join(BASE_DIR, "GuiadoCursoConsultorioHighTicket.-CHT21[1].pdf"))
_raw_pdf3 = read_pdf(os.path.join(BASE_DIR, "5.8 - Dossiê 007 - (3)[1].pdf"))
_raw_pdf4 = read_pdf(os.path.join(BASE_DIR, "Papelaria e brindes  lista de links e indicações.pdf"))

# -----------------------------
# PALAVRAS-CHAVE PARA CLASSIFICAÇÃO
# -----------------------------
TYPE_KEYWORDS = {
    "revisao":                        ["revisão", "revise", "resumir"],
    "precificacao":                   ["precificação", "precificar", "preço", "valor", "faturamento"],
    "health_plan":                    ["health plan", "retorno do investimento", "canva"],
    "capitacao_sem_marketing_digital": ["offline", "sem instagram", "sem anúncios", "sem redes sociais"],
    "aplicacao":                      ["como aplico", "aplicação", "roteiro"],
    "faq":                            ["quais", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "dossie":                         ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"],
    "papelaria":                      ["jo malone", "importadoras", "cafeteiras", "chocolates", "chás"],
    "playlist":                       ["playlist", "spotify"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS
# -----------------------------
CANONICAL_QA = {
    # — Health Plan (Canva) —
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo: "
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">Formulário Health Plan (Canva)</a>. "
        "Ele também está disponível diretamente na Aula 10.4 do curso Consultório High Ticket.",

    # — Patient Letter —
    "faz sentido mandar a patient letter para outros profissionais referente a pacientes antigos somente para pacientes novos devo mandar a patient letter em cada consulta do paciente por exemplo a cada retorno de 6 meses":
        "Olá, excelente pergunta!<br><br>"
        "Sim, faz sentido mandar um Patient Letter para outros profissionais referente a pacientes antigos, principalmente em caso de mudanças significativas no tratamento ou homenagens ao paciente. "
        "O intuito deste tipo de cartão é atualizar informações e marcar o cuidado e reconhecimento do seu trabalho com o paciente.<br><br>"
        "O mesmo vale para pacientes novos, como uma forma de demonstrar que você está acompanhando de perto o desenvolvimento do caso e se esforça para criá-los de forma personalizada, valorizando a relação construída.<br><br>"
        "No entanto, não é necessário enviar o Patient Letter ao final de todas as consultas, a não ser que haja alguma informação específica que necessita ser compartilhada. "
        "Você pode optar por enviá-lo quando ocorrer uma mudança expressiva no prontuário do paciente ou quando achar pertinente.<br><br>"
        "Lembre-se que o mais importante é manter a comunicação aberta e frequente com outros profissionais, garantindo um atendimento integrado e de excelência ao paciente.<br><br>"
        "Espero que isso te ajude, qualquer outra dúvida, estou à disposição! 💜",

    # — Respostas específicas de Patient Letter —
    "quando devo enviar uma patient letter para um colega especialista apos a primeira consulta de um paciente":
        "Envie a Patient Letter logo após a primeira consulta sempre que encaminhar o paciente a outro especialista. "
        "Isso garante que o colega receba histórico clínico, resultados de exames e plano de cuidado completo para continuidade do tratamento.",

    "o que fazer quando recebo uma patient letter de volta de um colega":
        "Para responder um Patient Letter recebido, adote a “mensagem de 20 segundos”:<br>"
        "<em>“Oi Dr(a). X, aqui é o Dr(a). Y. Recebi seu retorno sobre o paciente Z. Que tal conversarmos em 5 minutos às 14h ou às 15h?”</em><br>"
        "Essa abordagem fortalece o relacionamento e facilita futuras colaborações.",

    "posso entregar a patient letter em formato digital ou ela precisa ser manuscrita":
        "Você pode optar tanto por manuscrita quanto digital. Se manuscrita, use papel de qualidade e capriche na legibilidade; "
        "se digital, envie um PDF por e-mail ou WhatsApp, garantindo que constem nome, contato e informações essenciais. "
        "O importante é a clareza e a personalização da mensagem.",

    "como personalizo a patient letter para que ela seja bem recebida por outro profissional":
        "Personalize incluindo o nome completo do colega e do paciente no cabeçalho, seja objetiva com informações técnicas essenciais (exames, plano de tratamento), "
        "e finalize com convite para breve conversa:<br>"
        "<em>“Oi Dr(a). X, sou o Dr(a). Y. Atendi o paciente Z e gostaria de dar um retorno. Que tal falarmos 5 minutos às 15h ou 16h?”</em>."
        "Isso demonstra profissionalismo e cuidado.",

    "faz sentido mandar patient letter para pacientes que retornam ao consultorio depois de 6 meses":
        "Não é necessário enviar um Patient Letter em cada retorno de rotina sem novidades clínicas. "
        "Reserve o envio para quando houver mudanças significativas no tratamento ou nos resultados, mantendo a comunicação relevante.",
    
    # ... mantenha demais entradas canônicas existentes ...
}

# Pré-normaliza chaves
CANONICAL_QA_NORMALIZED = { normalize_key(k): v for k, v in CANONICAL_QA.items() }

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo "
    "do curso <strong>Consultório High Ticket</strong>. Responda como uma professora experiente, "
    "ajudando o aluno a aplicar o método na prática.<br><br>"
)

prompt_variacoes = {
    "explicacao": (
        "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. "
        "Use uma linguagem clara e didática, com tópicos ou passos. Evite genéricos.<br><br>"
    ),
    "faq": (
        "<strong>Objetivo:</strong> Responder de forma direta a dúvidas frequentes do curso. "
        "Use exemplos práticos e mencione etapas conforme o material."
    )
}

# -----------------------------
# CLASSIFICADOR E GERADOR DE RESPOSTA
# -----------------------------
def classify_prompt(question: str) -> dict:
    lower = normalize_key(question)
    if lower in CANONICAL_QA_NORMALIZED:
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}


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
        r = client.chat.completions.create(model="gpt-4", messages=[{"role":"user","content":prompt}])
    except OpenAIError:
        r = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
    return r.choices[0].message.content
