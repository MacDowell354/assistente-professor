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
    # Perguntas operacionais, se necessário
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
        return format_as_teacher(context)
    return OUT_OF_SCOPE_MSG

def format_as_teacher(context: str) -> str:
    import re
    texto = context.strip()
    texto = re.sub(r'(?m)^(\d+\.|\-|\•)', r'<br>\1', texto)
    texto = texto.replace('\n', '<br>')
    return (
        "<div style='line-height:1.7em;font-size:1.05em;'>"
        f"{texto.strip()}"
        "</div>"
    )
