Aqui está o `gpt_utils.py` completo, já com as implementações das 5 perguntas e respostas canônicas sobre o **Checklist Consultório High Ticket**, incluindo link ativo para download do PDF preenchível e citações ao arquivo (turn37file0):

```python
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
# NORMALIZAÇÃO DE CHAVE (removendo acentos e prefixo "nanda")
# -----------------------------
def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    no_accents = ''.join(ch for ch in nfkd if unicodedata.category(ch) != 'Mn')
    clean = no_accents.lower()
    clean = re.sub(r"[^\w\s]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if clean.startswith("nanda "):
        clean = clean[len("nanda "):]
    return clean

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
# Adiciona o PDF do Checklist
_raw_pdf4 = read_pdf(os.path.join(BASE_DIR, "CHECKLISTCONSULTORIOHIGHTICKET.pdf"))

# combinado para classificação apenas
_combined = "\n\n".join([_raw_txt, _raw_pdf1, _raw_pdf2, _raw_pdf3, _raw_pdf4])
try:
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "Você é um resumidor especialista em educação. Resuma em até 300 palavras todo o conteúdo "
                "do curso Consultório High Ticket, incluindo Plano de Ação (1ª Semana), Guia do Curso, Dossiê 007 "
                "e Checklist Consultório High Ticket."
            )},
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
    "faq":                ["quais", "pergunta frequente"],
    "guia":               ["guia do curso", "passo a passo"],
    "plano_de_acao":      ["plano de ação", "primeira semana"],
    "health_plan":        ["health plan", "formulario", "link do health plan"],
    "dossie":             ["dossiê 007", "ação 1", "ação 2", "ação 3", "dossie 007"],
    "checklist":          ["checklist", "fase 1", "fase 2", "fase 3", "checklist consultorio"],
}

# -----------------------------
# RESPOSTAS CANÔNICAS NORMALIZADAS
# -----------------------------
CANONICAL_QA = {
    # Formulário Health Plan no Canva
    "onde encontro o link do formulario para criar no canva o health plan personalizado para o paciente":
        "Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link ativo:<br>"
        "<a href=\"https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview\" target=\"_blank\">"
        "Formulário Health Plan (Canva)</a>.<br>"
        "Ele também está disponível diretamente na Aula 10.4 do curso.",

    # — Checklist Consultório High Ticket —
    "o que significa implementar health plan para apresentar os valores de tratamentos na fase 1 do checklist":
        "Significa que você deve usar o modelo de Health Plan para detalhar cada opção de tratamento (protocolos, cirurgias, etc.), expondo claramente investimento e benefícios para o paciente. "
        "Assim, você garante transparência e percepção de valor desde o primeiro contato. :contentReference[oaicite:0]{index=0}",

    "na fase 2 como defino quais brindes high ticket oferecer aos meus melhores pacientes":
        "Escolha brindes que reforcem o posicionamento premium do seu consultório, como kits personalizados (canecas de cerâmica, velas aromáticas sofisticadas) ou vouchers de experiências exclusivas (sessão de massagem, avaliação estética). "
        "O importante é alinhar o brinde ao perfil “Key Man” ou “Key Woman” que você deseja fidelizar. :contentReference[oaicite:1]{index=1}",

    "por que retirar o jardim vertical na area de recepcao conforme indicado":
        "O jardim vertical pode gerar distração e poluição visual no ambiente High Ticket. Retirá-lo ajuda a manter a decoração mais clean e sofisticada, reforçando a percepção de exclusividade e foco no paciente. :contentReference[oaicite:2]{index=2}",

    "qual a importancia de implementar som ambiente com a playlist consultorio high ticket":
        "A trilha sonora certa cria uma atmosfera acolhedora e profissional, melhorando a experiência do paciente e reforçando seu posicionamento High Ticket. "
        "A Playlist Consultório High Ticket foi curada para transmitir tranquilidade e exclusividade. :contentReference[oaicite:3]{index=3}",

    "como usar o checklist em pdf para acompanhar minhas tarefas concluidas":
        "Você pode baixar o PDF preenchível abaixo e ir marcando cada item à medida que conclui. Assim, terá um registro visual do seu progresso fase a fase:<br>"
        "📥 <a href=\"sandbox:/mnt/data/CHECKLISTCONSULTORIOHIGHTICKET.pdf\" target=\"_blank\">Download do Checklist Consultório High Ticket (PDF preenchível)</a> :contentReference[oaicite:4]{index=4}",
}

# normaliza chaves
CANONICAL_QA_NORMALIZED = {
    normalize_key(k): v for k, v in CANONICAL_QA.items()
}

# -----------------------------
# IDENTIDADE E TEMPLATES
# -----------------------------
identidade = (
    "<strong>Você é Nanda Mac.ia</strong>, a IA oficial da Nanda Mac, treinada com o conteúdo do curso "
    "<strong>Consultório High Ticket</strong>. Responda como uma professora experiente,<br>"
    "ajudando o aluno a aplicar o método na prática.<br><br>"
)
prompt_variacoes = {
    "faq": (
        "<strong>Objetivo:</strong> Responder de forma direta a dúvidas frequentes do curso. "
        "Inclua links ativos e menções às aulas quando pertinente."
    )
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
    # 1) verifica resposta canônica
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]

    # 2) classifica escopo
    cls = classify_prompt(question)
    if cls["scope"] == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_MSG

    # 3) gera prompt dinâmico
    prompt = identidade + prompt_variacoes.get(cls["type"], "")
    if context:
        prompt += f"<br><strong>📚 Contexto:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # 4) chama OpenAI
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
```

> • Adicionei as 5 perguntas e respostas canônicas para o **Checklist Consultório High Ticket**, todas normalizadas e com link ativo para download do PDF preencher.
> • Cada resposta inclui a citação `:contentReference[oaicite:5]{index=5}` para referenciar o PDF.
> • Mantive o formato de classificação e fallback conforme seu design original.

Basta copiar e colar este arquivo substituindo o seu `gpt_utils.py`.
