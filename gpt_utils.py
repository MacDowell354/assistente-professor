import os
import unicodedata
import re

OUT_OF_SCOPE_MSG = (
    "Sua pergunta demonstra interesse e vontade de aprender!<br>"
    "No entanto, esse tema ainda não faz parte do conteúdo oficial do curso <b>Consultório High Ticket</b>.<br>"
    "Recomendo focar nas estratégias, conceitos e práticas ensinadas nas aulas para transformar seu consultório.<br>"
    "Sua dúvida será encaminhada à equipe pedagógica para avaliarmos uma possível inclusão em futuras atualizações.<br>"
    "Continue participando!"
)

def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

CANONICAL_QA = {
    # Perguntas operacionais, se houver
}

CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]
    if context and len(context.strip()) > 20:
        return format_as_teacher(context, question)
    return OUT_OF_SCOPE_MSG

def format_as_teacher(context: str, question: str = "") -> str:
    import re

    # 1. Título: Se identificar título no início do contexto ou pela pergunta
    titulo = ""
    if question:
        # Ex: Como estruturo a apresentação do valor do Health Plan para que o paciente veja o retorno do investimento?
        titulo = "<b>" + question.strip().capitalize() + "</b><br><br>"
    else:
        # Busca por título natural no contexto
        match = re.match(r"^(.*?)([:：])", context)
        if match:
            titulo = "<b>" + match.group(1).strip() + ":</b><br><br>"

    # 2. Lista numerada: transforma passos (1., 2., etc.) em lista bonita
    texto = context.strip()
    texto = re.sub(r"(\n)?(\d+\.)(\s+)", r"<br><b>\2</b> ", texto)
    texto = re.sub(r"[\n\r]\s*[\-\•]\s*", r"<br>&bull; ", texto)

    # 3. Destaque em negrito palavras-chave comuns do método
    palavras_destaque = ["importante", "dica", "atenção", "exemplo", "finalize", "associe", "explique", "benefício", "passo", "resultado", "orientação", "plano", "etapa", "invista", "apresente"]
    for palavra in palavras_destaque:
        texto = re.sub(fr'\b({palavra})\b', r'<b>\1</b>', texto, flags=re.IGNORECASE)

    # 4. Quebra de linha para parágrafos e ajuste visual
    texto = texto.replace('\n', '<br>')
    texto = re.sub(r'(<br>\s*){2,}', '<br>', texto)

    return (
        "<div style='line-height:1.7em;font-size:1.08em; margin-bottom:12px;'>"
        f"{titulo}{texto.strip()}"
        "</div>"
    )
