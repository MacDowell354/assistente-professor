import os

OUT_OF_SCOPE_MSG = (
    "Sua pergunta demonstra interesse e vontade de aprender! No entanto, esse tema ainda não faz parte do conteúdo oficial do curso Consultório High Ticket. "
    "Recomendo focar nas estratégias, conceitos e práticas ensinadas nas aulas para transformar seu consultório. "
    "Sua dúvida será encaminhada à equipe pedagógica para avaliarmos uma possível inclusão em futuras atualizações. "
    "Continue participando!"
)

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    if context and len(context.strip()) > 20:
        return context.strip()
    return OUT_OF_SCOPE_MSG
