import os

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

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    if context and len(context.strip()) > 20:
        # Responde somente se contexto realmente mencionar áreas do curso
        if any(palavra in context.lower() for palavra in [
            "consultório", "high ticket", "paciente", "atendimento", "valorização", "captação", "secretária"
        ]):
            return f"<strong>Explicação com base no curso:</strong><br>{context.strip()}"
    return OUT_OF_SCOPE_MSG
