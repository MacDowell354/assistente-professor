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
    "capitacao_sem_marketing_digital":[ "offline", "sem instagram", "sem anúncios", "sem redes sociais"],
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
    # — Saudações como professora —
    "oi": (
        "Olá! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
        "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
        "Estou aqui para caminhar com você e esclarecer todas as suas dúvidas com base nas aulas do curso, "
        "como uma professora dedicada e experiente.<br><br>"
        "Meu objetivo é te ajudar a aplicar o método da Nanda com clareza, segurança e foco nos resultados."
        "<br><br>Pode perguntar o que quiser, que eu te explico como se estivéssemos em uma aula particular. 🥰"
    ),
    "ola":  # corresponde a 'olá'
        "Olá! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
        "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
        "Estou aqui para caminhar com você e esclarecer todas as suas dúvidas com base nas aulas do curso, "
        "como uma professora dedicada e experiente.<br><br>"
        "Meu objetivo é te ajudar a aplicar o método da Nanda com clareza, segurança e foco nos resultados."
        "<br><br>Pode perguntar o que quiser, que eu te explico como se estivéssemos em uma aula particular. 🥰",
    "bom dia":
        "Bom dia! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
        "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
        "Pronta para ajudar você a aplicar o método da Nanda com clareza e foco nos resultados. "
        "Pergunte o que quiser, como se estivéssemos em uma aula particular! 🥰",
    "boa tarde":
        "Boa tarde! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
        "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
        "Estou pronta para caminhar com você e esclarecer suas dúvidas de forma didática e prática. 🥰",
    "boa noite":
        "Boa noite! 😊 Seja muito bem-vindo ao seu espaço de aprendizado!<br><br>"
        "Eu sou a Nanda Mac.ia, sua professora virtual aqui no curso Consultório High Ticket. "
        "Aqui para ajudar você a aplicar o método da Nanda com segurança e foco nos resultados. 🥰",

    # — Health Plan (Canva) —
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo: "
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?"
        "utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">"
        "Formulário Health Plan (Canva)</a>. "
        "Ele também está disponível diretamente na Aula 10.4 do curso Consultório High Ticket.",

    # — Patient Letter —
    "faz sentido mandar a patient letter para outros profissionais referente a pacientes antigos":
        "Olá, excelente pergunta!<br><br>"
        "Sim, faz sentido mandar um Patient Letter para outros profissionais referente a pacientes antigos, principalmente em caso de mudanças significativas no tratamento ou homenagens ao paciente. "
        "O intuito deste tipo de cartão é atualizar informações e marcar o cuidado e reconhecimento do seu trabalho com o paciente.<br><br>"
        "O mesmo vale para pacientes novos, como uma forma de demonstrar que você está acompanhando de perto o desenvolvimento do caso e se esforça para criá-los de forma personalizada, valorizando a relação construída.<br><br>"
        "No entanto, não é necessário enviar o Patient Letter ao final de todas as consultas, a não ser que haja alguma informação específica que necessita ser compartilhada. "
        "Você pode optar por enviá-lo quando ocorrer uma mudança expressiva no prontuário do paciente ou quando achar pertinente.<br><br>"
        "Lembre-se que o mais importante é manter a comunicação aberta e frequente com outros profissionais, garantindo um atendimento integrado e de excelência ao paciente.<br><br>"
        "Espero que isso te ajude, qualquer outra dúvida, estou à disposição! 💜",

    # ... demais entradas canônicas existentes ...
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
    if any(canon_key in lower for canon_key in CANONICAL_QA_NORMALIZED):
        return {"scope": "IN_SCOPE", "type": "faq"}
    for t, kws in TYPE_KEYWORDS.items():
        if any(normalize_key(k) in lower for k in kws):
            return {"scope": "IN_SCOPE", "type": t}
    return {"scope": "OUT_OF_SCOPE", "type": "explicacao"}

def generate_answer(question: str, context: str = "", history: str = None, tipo_de_prompt: str = None) -> str:
    key = normalize_key(question)
    # lookup canônico por substring
    for canon_key, answer in CANONICAL_QA_NORMALIZED.items():
        if canon_key in key:
            return answer
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
        r = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
    except OpenAIError:
        r = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content
