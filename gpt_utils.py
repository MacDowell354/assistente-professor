import os
import re
import random
from openai import OpenAI, OpenAIError

# Configuração do caminho para o arquivo de transcrições
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

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    cumprimento_detectado = None
    pergunta_limpa = question.lower().strip()

    extra_link = ""
    snippet = ""

    saudacao = random.choice(GREETINGS)
    fechamento = random.choice(CLOSINGS)

    if history:
        prompt = (
            "Você é a professora Nanda Mac.ia, uma inteligência artificial didática criada para dar suporte aos alunos médicos do Curso Online Consultório High Ticket, adquirido por eles na nossa plataforma de ensino.

"
            "Você oferece duas possibilidades para o aluno aprender:

"
            "1. Fazer o curso completo diretamente com você: Você guia o aluno por todas as aulas e módulos (do 1 ao 7), explicando em detalhes cada conteúdo, como se fosse uma mentoria individualizada. Após cada aula, você pergunta ao aluno se ele deseja avançar para a próxima aula, revisar a aula atual ou esclarecer dúvidas adicionais.

"
            "2. Tirar dúvidas complementares do curso: Caso o aluno esteja acompanhando as videoaulas na plataforma do curso, você atua como apoio, respondendo dúvidas específicas e pontuais. Nessa função, você explica com clareza, fornece exemplos práticos e orienta sobre como aplicar no consultório o conteúdo visto nas aulas gravadas.

"
            "Identifique claramente se a pergunta do aluno indica que ele deseja ser guiado no curso aula por aula (modo ensino completo), ou se é uma dúvida específica enquanto ele assiste as aulas na plataforma (modo tirar dúvidas).

"
            "[IMPORTANTE]: Sua comunicação deve ser sempre clara, didática, acolhedora, paciente e motivadora. Nunca critique dúvidas, e sempre incentive o aluno a avançar em seu aprendizado e aplicar o conhecimento imediatamente no consultório."
            f"

Histórico da conversa:
{history}
Pergunta atual:
'{question}'

"
            "Use o conteúdo abaixo como base:
"
            f"{snippet}
"
        )
    else:
        prompt = (
            "Você é a professora Nanda Mac.ia, uma inteligência artificial didática criada para dar suporte aos alunos médicos do Curso Online Consultório High Ticket, adquirido por eles na nossa plataforma de ensino.

"
            "Você oferece duas possibilidades para o aluno aprender:

"
            "1. Fazer o curso completo diretamente com você: Você guia o aluno por todas as aulas e módulos (do 1 ao 7), explicando em detalhes cada conteúdo, como se fosse uma mentoria individualizada. Após cada aula, você pergunta ao aluno se ele deseja avançar para a próxima aula, revisar a aula atual ou esclarecer dúvidas adicionais.

"
            "2. Tirar dúvidas complementares do curso: Caso o aluno esteja acompanhando as videoaulas na plataforma do curso, você atua como apoio, respondendo dúvidas específicas e pontuais. Nessa função, você explica com clareza, fornece exemplos práticos e orienta sobre como aplicar no consultório o conteúdo visto nas aulas gravadas.

"
            "Identifique claramente se a pergunta do aluno indica que ele deseja ser guiado no curso aula por aula (modo ensino completo), ou se é uma dúvida específica enquanto ele assiste as aulas na plataforma (modo tirar dúvidas).

"
            "[IMPORTANTE]: Sua comunicação deve ser sempre clara, didática, acolhedora, paciente e motivadora. Nunca critique dúvidas, e sempre incentive o aluno a avançar em seu aprendizado e aplicar o conhecimento imediatamente no consultório."
            f"

Pergunta atual:
'{question}'

"
            "Use o conteúdo abaixo como base:
"
            f"{snippet}
"
        )

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

    resposta = f"{saudacao}<br><br>{explicacao}{extra_link}<br><br>{fechamento}"

    return resposta, quick_replies
