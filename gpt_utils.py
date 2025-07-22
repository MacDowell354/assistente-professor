import os
import re
import random
from openai import OpenAI, OpenAIError

# Configurar seu arquivo de transcrições
TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")

client = OpenAI()

OUT_OF_SCOPE_MSG = (
    "Desculpe, ainda não tenho informações suficientes sobre esse tema específico do curso. "
    "Por favor, envie outra pergunta ou consulte o material da aula."
)

GREETINGS = [
    "Olá, Doutor(a), seja muito bem-vindo(a)!",
    "Oi, Doutor(a), tudo bem? Como posso ajudar?",
    "Bem-vindo(a) de volta, Doutor(a)!",
    "Olá, Doutor(a)! Estou aqui para apoiar você no seu crescimento"
]

CLOSINGS = [
    "Se quiser um exemplo prático ou modelo, clique nos botões abaixo.",
    "Tem outro desafio no seu consultório? Me conte ou clique em Novo Tema.",
    "Se quiser aprofundar, escolha uma opção rápida ou pergunte de novo!",
    "Quer mudar de assunto? Só digitar ‘novo tema’.",
    "Essa resposta te ajudou? Clique em 👍 ou 👎."
]

CUMPRIMENTOS_RESPOSTAS = {
    "bom dia": "Bom dia! Se quiser tirar dúvidas sobre o curso, é só perguntar. Estou à disposição.",
    "boa tarde": "Boa tarde! Se quiser tirar dúvidas sobre o curso, é só perguntar. Estou à disposição.",
    "boa noite": "Boa noite! Estou aqui para ajudar. Pode enviar sua dúvida quando quiser.",
    "oi": "Oi, Doutor(a)! 😊 Seja bem-vindo(a)! Pode enviar sua dúvida quando quiser.",
    "olá": "Olá! Estou aqui para ajudar. Pode perguntar sobre Consultório High Ticket quando quiser!",
    "ola": "Olá! Estou aqui para ajudar. Pode perguntar sobre Consultório High Ticket quando quiser!",
    "tudo bem": "Tudo ótimo por aqui! Se quiser perguntar algo sobre o curso, fique à vontade.",
    "oi, tudo bem": "Oi, tudo bem! Se quiser tirar dúvidas, pode perguntar que estou à disposição.",
    "e aí": "E aí! Se quiser tirar dúvidas sobre o curso, estou por aqui para te ajudar."
}

# Lista de perguntas/chips que nunca devem receber saudação ou repetição
CHIP_PERGUNTAS = [
    "Ver Exemplo de Plano", "Modelo no Canva", "Modelo PDF", "Novo Tema",
    "Preciso de exemplo", "Exemplo para Acne", "Tratamento Oral", "Cuidados Diários",
    "Baixar Plano de Ação", "Baixar Guia do Curso"
]

def is_greeting(question):
    pergunta = question.strip().lower()
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta == c or pergunta.startswith(c):
            return c
    return None

def remove_greeting_from_question(question):
    pergunta = question.strip().lower()
    for c in CUMPRIMENTOS_RESPOSTAS.keys():
        if pergunta.startswith(c):
            pergunta_sem_cumprimento = pergunta[len(c):].lstrip(" ,.!?;-")
            return pergunta_sem_cumprimento
    return pergunta

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def search_transcripts_by_theme(theme):
    theme_norm = normalize_text(theme)
    if not os.path.exists(TRANSCRIPTS_PATH):
        return None

    with open(TRANSCRIPTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content_norm = normalize_text(content)
    pos = content_norm.find(theme_norm)
    if pos == -1:
        palavras = theme_norm.split()
        for palavra in palavras:
            pos = content_norm.find(palavra)
            if pos != -1:
                break
        else:
            return None

    start = max(0, pos - 500)
    end = min(len(content), pos + 500)
    snippet = content[start:end]
    return snippet.strip()

def gerar_quick_replies(question, explicacao, history=None):
    """
    Sugere quick replies (chips) de acordo com o tema original e histórico de uso.
    Chips essenciais (ex: Modelo no Canva, Baixar Plano de Ação, Baixar Guia do Curso) permanecem até o usuário utilizar.
    """
    base_replies = ["Novo Tema", "Preciso de exemplo"]
    # Detecta o TEMA da conversa (olhando o início do histórico)
    tema_healthplan = False
    tema_acne = False
    tema_plano_acao = False
    tema_guia_curso = False

    # Palavras-chave para plano de ação/onboarding e guia do curso
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]

    if history and isinstance(history, list) and len(history) > 0:
        # Busca a PRIMEIRA pergunta do aluno para identificar o contexto geral
        for msg in history:
            if "user" in msg and isinstance(msg["user"], str):
                q = msg["user"].lower()
                if any(x in q for x in ["health plan", "healthplan", "realplan"]):
                    tema_healthplan = True
                    break
                elif "acne" in q:
                    tema_acne = True
                    break
                elif any(x in q for x in PLANO_ACAO_KEYWORDS):
                    tema_plano_acao = True
                    break
                elif any(x in q for x in GUIA_CURSO_KEYWORDS):
                    tema_guia_curso = True
                    break
    else:
        q = question.lower()
        if any(x in q for x in ["health plan", "healthplan", "realplan"]):
            tema_healthplan = True
        elif "acne" in q:
            tema_acne = True
        elif any(x in q for x in PLANO_ACAO_KEYWORDS):
            tema_plano_acao = True
        elif any(x in q for x in GUIA_CURSO_KEYWORDS):
            tema_guia_curso = True

    replies = []
    if tema_healthplan:
        replies += ["Ver Exemplo de Plano", "Modelo no Canva"]
    elif tema_acne:
        replies += ["Exemplo para Acne", "Tratamento Oral", "Cuidados Diários"]
    if tema_plano_acao:
        replies += ["Baixar Plano de Ação"]
    if tema_guia_curso:
        replies += ["Baixar Guia do Curso"]
    if not replies:
        replies = base_replies

    # Controle de histórico: identifica chips já usados
    usados = set()
    if history and isinstance(history, list):
        for msg in history:
            # Se o usuário clicou em um chip
            if "chip" in msg and msg["chip"]:
                usados.add(msg["chip"].strip().lower())
            # Ou se já digitou igual ao chip sugerido anteriormente
            if "user" in msg and msg["user"]:
                u = msg["user"].strip().lower()
                if u in [x.lower() for x in replies]:
                    usados.add(u)
    # Chips essenciais
    ESSENCIAIS = ["modelo no canva", "baixar plano de ação", "baixar guia do curso"]
    filtered = []
    for r in replies:
        if r.lower() in ESSENCIAIS:
            # Só some se já usado
            if r.lower() not in usados:
                filtered.append(r)
        else:
            if r.lower() not in usados:
                filtered.append(r)
    # Garante pelo menos opções básicas
    if len(filtered) < 2:
        filtered += [r for r in base_replies if r not in filtered]
    return filtered[:3]

def generate_answer(
    question, context="", history=None, tipo_de_prompt=None, is_first_question=True
):
    cumprimento_detectado = is_greeting(question)
    pergunta_limpa = remove_greeting_from_question(question)

    # Só responde cumprimento simples
    if cumprimento_detectado and not pergunta_limpa.strip():
        return CUMPRIMENTOS_RESPOSTAS[cumprimento_detectado], []

    # --- RESPOSTA ESPECIAL: PDF PLANO DE AÇÃO ONBOARDING ---
    PLANO_ACAO_KEYWORDS = [
        "plano de ação", "pdf plano de ação", "atividade da primeira semana",
        "material do onboarding", "ação consultório", "plano onboarding",
        "plano de ação consultório", "atividade plano", "baixar plano de ação"
    ]
    pergunta_baixar_plano = any(x in pergunta_limpa for x in PLANO_ACAO_KEYWORDS) or \
        (question and any(x in question.lower() for x in PLANO_ACAO_KEYWORDS))

    if pergunta_baixar_plano or (question.strip().lower() == "baixar plano de ação"):
        resposta = (
            "<strong>Plano de Ação do Consultório High Ticket</strong><br>"
            "Esse material faz parte do onboarding do curso e é essencial para você organizar seus próximos passos.<br><br>"
            "<b>O que você vai encontrar nesse PDF:</b><br>"
            "- Reflexão sobre bloqueios financeiros e autoconfiança<br>"
            "- Definição de nicho de atuação e ajustes de posicionamento<br>"
            "- Planejamento de ações práticas para atrair pacientes High Ticket já na primeira semana<br>"
            "- Exercícios para transformar sua mentalidade e o consultório<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EV6wZ42I9nhHpmnSGa4DHfEBaff0ewZIsmH_4LqLAI46eQ?e=gd5hR0' target='_blank'>📄 Baixar Plano de Ação do Consultório High Ticket</a><br><br>"
            "Você também pode baixar esse PDF dentro do módulo de onboarding, na sua área de alunos.<br>"
            "Se tiver dificuldade para acessar, me avise que envio suporte!"
        )
        return resposta, []

    # --- RESPOSTA ESPECIAL: PDF GUIA DO CURSO CHT ---
    GUIA_CURSO_KEYWORDS = [
        "guia do curso", "guia cht", "guia consultório high ticket",
        "manual do curso", "manual cht", "material de onboarding",
        "passos iniciais", "guia onboarding", "baixar guia do curso"
    ]
    pergunta_guia_curso = any(x in pergunta_limpa for x in GUIA_CURSO_KEYWORDS) or \
        (question and any(x in question.lower() for x in GUIA_CURSO_KEYWORDS))
    if pergunta_guia_curso or (question.strip().lower() == "baixar guia do curso"):
        resposta = (
            "<strong>Guia do Curso Consultório High Ticket</strong><br>"
            "Esse material é essencial para te orientar nos primeiros passos do curso, desde o onboarding até as tarefas e integração na comunidade.<br><br>"
            "<b>O que você encontra nesse guia:</b><br>"
            "- Passo a passo para assistir à aula de onboarding<br>"
            "- Como entrar no grupo de avisos da sua turma<br>"
            "- Como acessar a área de membros e comunidade<br>"
            "- Detalhes sobre o Desafio Health Plan<br>"
            "- Como participar das atividades da primeira semana<br>"
            "- Canais de suporte e regras de uso<br><br>"
            "<a class='chip' href='https://nandamac-my.sharepoint.com/:b:/p/lmacdowell/EQZrQJpHXlVCsK1N5YdDIHEBHocn7FR2yQUHhydgN84yOw?e=GAut9r' target='_blank'>📄 Baixar Guia do Curso Consultório High Ticket</a><br><br>"
            "Você também pode encontrar esse PDF fixado no módulo de onboarding da sua área de alunos.<br>"
            "Se precisar de ajuda para acessar, me avise por aqui!"
        )
        return resposta, []

    # Evita saudação/repetição para chips
    is_chip = any(question.strip().lower() == c.lower() for c in CHIP_PERGUNTAS)
    mostrar_saudacao = is_first_question and not is_chip
    mostrar_pergunta_repetida = is_first_question and not is_chip

    saudacao = random.choice(GREETINGS) if mostrar_saudacao else ""
    fechamento = random.choice(CLOSINGS)

    # --- RESPOSTA ESPECIAL: "Modelo no Canva" para Health Plan/RealPlan ---
    if question.strip().lower() == "modelo no canva":
        # Busca o TEMA da conversa (primeira pergunta relevante do histórico)
        tema_healthplan = False
        if history and isinstance(history, list):
            for msg in history:
                if "user" in msg and isinstance(msg["user"], str):
                    q = msg["user"].lower()
                    if any(x in q for x in ["health plan", "healthplan", "realplan"]):
                        tema_healthplan = True
                        break
        else:
            q = question.lower()
            if any(x in q for x in ["health plan", "healthplan", "realplan"]):
                tema_healthplan = True

        if tema_healthplan:
            resposta = (
                "Aqui está o modelo de Health Plan para você adaptar ao seu consultório:<br>"
                "<strong>Esse modelo é 100% editável:</strong> faça uma cópia no Canva, preencha com os dados do seu paciente e adapte conforme a sua especialidade (psicologia, nutrição, dermato, etc.).<br>"
                "Basta clicar no botão abaixo, fazer login gratuito no Canva e, em seguida, clicar em ‘Usar este modelo’ para editar conforme sua especialidade.<br>"
                "<a class='chip' href='https://www.canva.com/design/DAEteeUPSUQ/0isBewvgUTJF0gZaRYZw2g/view?utm_content=DAEteeUPSUQ&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink&mode=preview' target='_blank'>Abrir Modelo no Canva</a>"
            )
            return resposta, []
        else:
            resposta = (
                "No momento, este recurso está disponível apenas para dúvidas sobre Health Plan. "
                "Se precisar de ajuda com outro tema, posso te orientar a criar um modelo personalizado!"
            )
            return resposta, []

    snippet = search_transcripts_by_theme(pergunta_limpa if pergunta_limpa.strip() else question)
    pergunta_repetida = (
        f"<strong>Sua pergunta:</strong> \"{question}\"<br><br>" if mostrar_pergunta_repetida else ""
    )

    if history:
        prompt = (
            f"Você é Nanda Mac.ia, professora do curso Consultório High Ticket.\n"
            f"Abaixo está a conversa até agora entre o aluno e a professora:\n\n"
            f"{history}\n\n"
            f"O aluno enviou agora:\n"
            f"'{question}'\n\n"
            "Continue a conversa considerando o contexto anterior. Se o aluno pedir mais detalhes, exemplos, ou disser 'mais específico', aprofunde sobre o assunto que estavam conversando, sem mudar de tema e sem repetir tudo do zero."
            "\nSe for uma dúvida nova, responda normalmente."
            "\n[IMPORTANTE] Seja didática, acolhedora e responda exatamente ao que o aluno pediu."
            "\nUtilize o conteúdo abaixo como base para a resposta:\n"
            f"{snippet}\n"
        )
    else:
        prompt = (
            f"Você é Nanda Mac.ia, professora do curso Consultório High Ticket.\n"
            f"O aluno fez a seguinte pergunta:\n\n"
            f"'{question}'\n\n"
            "Responda de forma extremamente objetiva e didática, exatamente como faria numa aula particular.\n"
            "Forneça uma resposta estruturada em tópicos numerados, utilizando exemplos práticos e claros.\n"
            "Use APENAS o conteúdo fornecido abaixo como referência e responda diretamente à pergunta feita,\n"
            "sem introduções ou divagações gerais:\n\n"
            f"{snippet}\n\n"
            "[IMPORTANTE] Seja objetiva, acolhedora e responda EXCLUSIVAMENTE ao tema solicitado."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )

    explicacao = response.choices[0].message.content.strip()
    quick_replies = gerar_quick_replies(question, explicacao, history)

    resposta = ""
    if mostrar_saudacao:
        resposta += f"{saudacao}<br><br>{pergunta_repetida}{explicacao}<br><br>{fechamento}"
    else:
        resposta += f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies
