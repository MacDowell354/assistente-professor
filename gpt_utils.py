import os
import re
import random
from openai import OpenAI, OpenAIError

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

def gerar_quick_replies(question, explicacao, history=None):
    return [
        "Quero um exemplo prático",
        "Me explique passo a passo",
        "Tenho uma dúvida sobre esse tema"
    ]

def resposta_link(titulo, url, icone="📄"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def resposta_link_externo(titulo, url, icone="🔗"):
    return f"<br><a class='chip' href='{url}' target='_blank'>{icone} {titulo}</a>"

def detectar_cenario(pergunta: str) -> str:
    pergunta = pergunta.lower()
    if any(p in pergunta for p in ["quero fazer o curso completo", "começar do início", "me ensina tudo", "fazer o curso com você"]):
        return "curso_completo"
    elif any(p in pergunta for p in ["quero começar pelo módulo", "me mostra o módulo", "ver o módulo", "começar módulo"]):
        return "modulo_especifico"
    elif any(p in pergunta for p in ["assisti", "já vi a aula", "tenho uma dúvida", "não entendi", "poderia explicar melhor"]):
        return "duvida_pontual"
    elif any(p in pergunta for p in ["exemplo prático", "me dá um exemplo", "passo a passo", "como fazer isso"]):
        return "exemplo_pratico"
    else:
        return "geral"

def atualizar_progresso(pergunta: str, progresso: dict) -> dict:
    if not progresso:
        return {'modulo': 1, 'aula': '1.1', 'etapa': 1}
    if pergunta.lower().strip() in ["sim", "sim desejo", "quero sim", "vamos", "ok"]:
        if progresso['etapa'] == 1:
            progresso['etapa'] = 2
        elif progresso['etapa'] == 2:
            progresso['etapa'] = 3
        else:
            modulo = progresso['modulo']
            num_atual = float(progresso['aula'])
            num_proxima = round(num_atual + 0.1, 1)
            progresso['aula'] = f"{modulo}.{int(num_proxima * 10) % 10}"
            progresso['etapa'] = 1
    return progresso

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    # RECUPERA PROGRESSO DO HISTÓRICO
    if history and isinstance(history, list) and len(history) > 0:
        ultimo_item = history[-1]
        progresso = ultimo_item.get('progresso', None)
        if not progresso:
            progresso = {'modulo': 1, 'aula': '1.1', 'etapa': 1}
    else:
        progresso = {'modulo': 1, 'aula': '1.1', 'etapa': 1}

    progresso = atualizar_progresso(question, progresso)
    modulo = progresso.get('modulo', 1)
    aula = progresso.get('aula', '1.1')
    etapa = progresso.get('etapa', 1)

    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)

    cenario = detectar_cenario(question)

    # *** MELHORIA: resposta didática para pedido de curso completo ***
    if cenario == "curso_completo":
        explicacao = (
            f"{saudacao}<br><br>"
            "Ótima decisão, doutor(a)! O curso Consultório High Ticket é composto por 7 módulos completos e progressivos. "
            "Você vai aprender desde a mentalidade e posicionamento high ticket, passando pela experiência do paciente, estratégias de fidelização e vendas, até técnicas específicas para cada especialidade.<br><br>"
            "Podemos avançar juntos, módulo por módulo, começando agora pelo Módulo 01 – Mentalidade High Ticket, ou você pode pedir para ir direto ao módulo que desejar.<br><br>"
            "Deseja iniciar imediatamente a primeira aula do Módulo 01?<br>"
            "Se quiser ver a lista detalhada de todos os módulos e aulas, é só pedir: <b>“Quero ver todos os módulos”</b>.<br><br>"
            f"{fechamento}"
        )
        quick_replies = gerar_quick_replies(question, explicacao, history)
        return explicacao, quick_replies, progresso

    if cenario == "modulo_especifico":
        # Lógica de apresentação didática do módulo, não só do índice.
        explicacao = (
            f"{saudacao}<br><br>"
            "Ótima escolha! Me diga qual módulo deseja começar, ou escreva o número do módulo e eu apresento uma visão clara das aulas e objetivos dele para você.<br>"
            "Por exemplo: 'Quero começar pelo módulo 06' ou 'Me mostre o módulo de vendas'.<br><br>"
            f"{fechamento}"
        )
        quick_replies = gerar_quick_replies(question, explicacao, history)
        return explicacao, quick_replies, progresso

    # Demais cenários (inclui o fluxo original completo!)
    if etapa == 1:
        instruction = f"Você está iniciando a aula {aula} do módulo {modulo}. Apresente o objetivo da aula, como uma introdução didática clara e bem estruturada. Explique por que o conteúdo é importante para o médico e qual será o impacto na prática clínica."
    elif etapa == 2:
        instruction = f"Você está na parte intermediária da aula {aula} do módulo {modulo}. Aprofunde o conteúdo com exemplos práticos, aplicações clínicas e orientações detalhadas para médicos. Use linguagem objetiva e densa."
    else:
        instruction = f"Você está encerrando a aula {aula} do módulo {modulo}. Recapitule os principais aprendizados e prepare o aluno para a próxima aula. Pergunte se ele deseja seguir para a aula seguinte."

    prompt = f"""{instruction}

Você é a professora Nanda Mac.ia, uma inteligência artificial altamente didática, criada especificamente para ensinar e tirar dúvidas de médicos que estudam o Curso Online Consultório High Ticket, ministrado por Nanda Mac Dowell.

Leia atentamente o histórico da conversa antes de responder, compreendendo o contexto exato da interação atual para garantir precisão na sua resposta.

ESTRUTURA COMPLETA DO CURSO – MÓDULOS E AULAS:

[SEU BLOCO DE MÓDULOS INTEIRO, COMO JÁ ESTÁ]

Histórico da conversa anterior:
{history}

Pergunta atual do aluno:
'{question}'

Utilize o conteúdo adicional abaixo, se relevante:
{context}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=700
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Responda SEMPRE em português do Brasil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=700
        )

    explicacao = response.choices[0].message.content.strip()
    quick_replies = gerar_quick_replies(question, explicacao, history)

    if saudacao:
        resposta = f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"
    else:
        resposta = f"{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies, progresso
