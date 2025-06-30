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

# Opcional: uso para gerar resumo via LLM
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um resumidor especialista em educação. Resuma em até 300 palavras "
                    "todo o conteúdo do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), "
                    "Guia do Curso e Dossiê 007."
                )
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
    "capitacao_sem_marketing_digital": ["offline", "sem instagram", "sem anúncios", "sem redes sociais"],
    "aplicacao":                      ["como aplico", "aplicação", "roteiro"],
    "faq":                            ["quais", "pergunta frequente"],
    "explicacao":                     ["explique", "o que é", "defina", "conceito"],
    "plano_de_acao":                  ["plano de ação", "primeira semana"],
    "guia":                           ["guia do curso", "passo a passo", "cht21"],
    "dossie":                         ["dossiê 007", "acao 1", "acao 2", "acao 3", "orientações finais"],
    "papelaria":                      ["jo malone", "importadoras", "cafeteiras", "chocolates", "chás"]
}

# -----------------------------
# RESPOSTAS CANÔNICAS
# -----------------------------
CANONICAL_QA = {
    # — Captação sem redes sociais —
    "e possivel atrair pacientes sem usar redes sociais":
        "Sim! Um dos pilares do curso Consultório High Ticket é justamente mostrar que "
        "é possível atrair pacientes fiéis e de alto valor sem depender de redes sociais. "
        "A Nanda ensina estratégias presenciais, indicações qualificadas, posicionamento de autoridade "
        "e um método validado que funciona offline, baseado em relacionamento e experiência. "
        "Você aprenderá tudo isso nas aulas, especialmente nas que tratam de captação sem marketing digital.",

    # — Comunidade —
    "como entro na comunidade high ticket":
        "A Comunidade High Ticket Doctors está dentro da plataforma do curso. Assim que você receber "
        "o e-mail com o título “Chegou seu acesso”, cadastre sua senha. Depois de logado, preencha seu perfil "
        "e entre na Comunidade para tirar dúvidas sobre o método, fazer networking e participar das oficinas.",

    # — Suporte urgente —
    "se eu tiver um problema urgente durante o curso como solicito suporte rapidamente":
        "Em caso de urgência no curso, envie um e-mail para **ajuda@nandamac.com** com o assunto “S.O.S Crise” "
        "para receber suporte em até 24 h úteis.",

    # — Dúvidas metodológicas —
    "onde devo postar minhas duvidas sobre o metodo do curso":
        "Todas as dúvidas metodológicas devem ser postadas exclusivamente na Comunidade da Área de Membros. "
        "Não use Direct, WhatsApp ou outros canais para questionar o método; assim sua pergunta fica visível "
        "a todos e recebe resposta mais rápida.",

    # — Plano de Ação (1ª Semana) —
    "no exercicio de bloqueios com dinheiro como escolho qual bloqueio priorizar e defino minha atitude dia do chega":
        "Identifique qual sentimento de culpa ao cobrar mais te afeta (a “Síndrome do Sacerdote”) e coloque-o como bloqueio prioritário. "
        "Em ‘Onde quero chegar’, escreva uma ação concreta, por exemplo: “A partir de hoje, afirmarei meu valor em cada consulta.”",

    "na parte de autoconfianca profissional o que devo escrever como atitude para nao deixar certas situacoes me abalar":
        "Liste duas experiências que minaram sua confiança. "
        "Em ‘Onde quero chegar’, defina uma ação transformadora, por exemplo: “Sempre que receber uma crítica, realizarei uma sessão de feedback construtivo com um colega.”",

    "como uso a atividade de nicho de atuacao para definir meu foco e listar as acoes necessarias":
        "Posicionamento Atual: descreva seus pontos fortes e lacunas. "
        "Nicho Ideal: defina quem são seus “pacientes-sonho”. "
        "Ações: liste etapas específicas com prazo, por exemplo: “Especializar em [X] em 3 meses.”, “Criar pacote online de avaliação inicial até o próximo mês.”, “Revisar site e materiais de comunicação em 2 semanas.”",

    "no valor da consulta e procedimentos como encontro referencias de mercado e defino meus valores atuais e ideais":
        "Anote seus preços atuais e pesquise médias de associações ou colegas. "
        "Defina seus valores ideais justificando seu diferencial, por exemplo: “R$ 300 por sessão de fisioterapia clínica, pois ofereço acompanhamento personalizado e relatório de progresso.”",

    "ainda nao tenho pacientes particulares qual estrategia de atracao high ticket devo priorizar e como executar na agenda":
        "Reserve um bloco fixo na agenda (ex.: toda segunda, das 8h–10h) para:\n"
        "1. Enviar 5 mensagens personalizadas a potenciais pacientes do seu nicho, usando o script do curso.\n"
        "2. Após iniciar atendimentos, implemente a Patient Letter: envie um convite impresso com seu nome, valor e benefícios, para reforçar o contato.",

    # — Papelaria & Brindes —
    "onde encontro produtos jo malone no brasil":
        "Você pode encontrar os aromas de ambiente Jo Malone no Brasil diretamente no site oficial:\n"
        "https://www.jomalone.com.br\n"
        "Lá estão disponíveis colônias como Blackberry & Bay, Wood Sage & Sea Salt, Lime Basil & Mandarin e Nectarine Blossom & Honey, além de velas e sabonetes.",

    "quais importadoras posso usar para comprar produtos que nao encontro no brasil":
        "Para produtos que não são facilmente encontrados aqui, você pode recorrer a importadoras como:\n"
        "• Easy to go Orlando: https://easytogoorlando.com/\n"
        "Ou fazer pedidos em grandes marketplaces internacionais, como a Amazon.",

    "quais marcas de cafeteiras foram mencionadas na aula":
        "As marcas de cafeteiras recomendadas durante o módulo são:\n"
        "• Delonghi\n"
        "• Nespresso\n"
        "• Breville",

    "onde posso comprar os chocolates indicados no curso":
        "Os chocolates mencionados foram:\n"
        "• Läderach\n"
        "• Daim\n"
        "Você os encontra em chocolaterias especializadas ou através de lojas online/importadoras.",

    "quais opcoes de chas foram indicadas no material":
        "Foram indicados dois tipos de chá:\n"
        "• New English Teas Vintage Victorian Round Tea Caddy\n"
        "• Twinings Earl Grey Loose Tea Tins"
    # ... mantenha as demais entradas canônicas originais ...
}

# Pré-normaliza chaves
CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

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
# CLASSIFICADOR
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
# GERADOR DE RESPOSTA
# -----------------------------
def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)

    # 0) Exercícios não fazem parte, exceto as canônicas
    if "exercicio" in key and key not in CANONICAL_QA_NORMALIZED:
        return OUT_OF_SCOPE_MSG

    # 1) Resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) Classifica escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) Monta prompt
    tipo = cls["type"]
    prompt = identidade + prompt_variacoes.get(tipo, "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += (
        f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br>"
        f"<strong>🧠 Resposta:</strong><br>"
    )

    # 4) Chama OpenAI (com fallback)
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
