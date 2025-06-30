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

# Apenas para perguntas MUITO operacionais, como link do Health Plan
CANONICAL_QA = {
    "onde encontro o link do formulario health plan":
        'Você pode acessar o formulário para criar seu Health Plan personalizado no Canva através deste link: '
        '<a href="https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview" target="_blank">Formulário Health Plan (Canva)</a>.',
    # Outras perguntas operacionais, se necessário...
}

CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

# PROMPT GLOBAL: sempre responder como professora, em português, didático e em tópicos
PROMPT_PROFESSORA = (
    "Você é uma professora experiente do curso Consultório High Ticket. "
    "Responda de forma didática, detalhada e acolhedora, sempre em português do Brasil. "
    "Utilize tópicos, listas, exemplos práticos, e explique passo a passo, como em uma verdadeira aula para alunos profissionais da saúde. "
    "Use somente as informações do curso abaixo."
)

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
        # Gera a resposta em formato didático (professora) sempre
        return format_as_teacher(context)
    return OUT_OF_SCOPE_MSG

def format_as_teacher(context: str) -> str:
    """
    Formata o contexto em formato didático de professora: parágrafos, listas, tópicos, negritos.
    """
    # Simples: transforma quebras de linha em <br> e adiciona destaques básicos
    # (Se quiser usar LLM para reescrever, adapte aqui)
    import re
    texto = context.strip()
    texto = re.sub(r'(?m)^(\d+\.|\-|\•)', r'<br>\1', texto)  # Quebra linhas em listas numeradas ou bullets
    texto = texto.replace('\n', '<br>')  # Força quebra de linha para parágrafos
    return (
        "<div style='line-height:1.7em;font-size:1.05em;'>"
        f"{PROMPT_PROFESSORA}<br><br>"
        f"{texto.strip()}"
        "</div>"
    )
