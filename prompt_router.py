def inferir_tipo_de_prompt(pergunta: str) -> str:
    pergunta_lower = pergunta.lower()

    if (
        "health plan" in pergunta_lower
        or "plano de tratamento" in pergunta_lower
        or "meu health plan" in pergunta_lower
        or "dúvida no health" in pergunta_lower
        or "como montar meu health" in pergunta_lower
        or ("sou pediatra" in pergunta_lower and "health" in pergunta_lower)
    ):
        return "health_plan"

    if "preço" in pergunta_lower or "valor" in pergunta_lower or "cobrar" in pergunta_lower or "precificar" in pergunta_lower:
        return "precificacao"

    if "atrair pacientes" in pergunta_lower or "sem marketing" in pergunta_lower or "sem instagram" in pergunta_lower:
        return "capitacao_sem_marketing_digital"

    if "como aplicar" in pergunta_lower or "exemplo prático" in pergunta_lower or "na prática" in pergunta_lower:
        return "aplicacao"

    if "errei" in pergunta_lower or "confundi" in pergunta_lower or "não entendi" in pergunta_lower:
        return "correcao"

    if "resumo" in pergunta_lower or "revisão" in pergunta_lower:
        return "revisao"

    if "muitos perguntam" in pergunta_lower or "pergunta comum" in pergunta_lower:
        return "faq"

    return "explicacao"
