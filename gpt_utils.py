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
    # Coloque aqui perguntas operacionais ou fixas, se desejar.
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

    # Negrito no título/frase inicial se houver dois pontos
    texto = re.sub(r"^(.*?)([:：])", r"<b>\1\2</b>", texto, 1)

    # Transformar listas numeradas (1., 2., 3.) em tópicos com negrito
    texto = re.sub(r"(\d+\.)(\s*)", r"<br><b>\1</b> ", texto)

    # Transformar bullets ("-", "•") em lista não numerada
    texto = re.sub(r"[\n\r]\s*[\-\•]\s*", r"<br>&bull; ", texto)

    # Quebra de linha para parágrafos
    texto = texto.replace('\n', '<br>')

    # Evitar múltiplos <br>
    texto = re.sub(r'(<br>\s*){2,}', '<br>', texto)

    # Caixa um pouco maior e espaçamento agradável
    return (
        "<div style='line-height:1.7em;font-size:1.07em; margin-bottom:12px;'>"
        f"{texto.strip()}"
        "</div>"
    )
