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

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    snippet = ""
    
    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)

    prompt = f"""
    Você é a professora Nanda Mac.ia, uma IA didática que guia alunos médicos pelo Curso Online Consultório High Ticket.

    Leia cuidadosamente o histórico da conversa para entender o contexto atual.

    Regras importantes para sua resposta:
    - Se o aluno pedir explicitamente por "um exemplo prático", "explicar passo a passo" ou "tem dúvidas sobre esse tema", SEMPRE aprofunde no conteúdo da AULA ATUAL. Nunca avance para a próxima aula antes de resolver essa solicitação.
    - Exemplo prático, passo a passo ou dúvidas SEMPRE devem referir-se diretamente ao conteúdo que acabou de ser ensinado, garantindo total clareza e aplicação prática no consultório do aluno.
    - Somente avance para a próxima aula quando o aluno claramente indicar que deseja avançar, usando frases como "próxima aula", "vamos continuar", "quero avançar" etc.
    - NÃO use novamente saudações como "Oi, Doutor(a), tudo bem?" ou "Como posso ajudar?" após a primeira interação. Vá diretamente ao ponto, mantendo coerência absoluta com o fluxo da aula.

    Histórico anterior da conversa:
    {history}

    Mensagem atual do aluno:
    '{question}'

    Com base nisso, aprofunde diretamente o conteúdo atual com exemplos práticos ou explicações detalhadas sobre o MESMO assunto ensinado anteriormente. NÃO avance para a próxima aula ainda.

    Use o conteúdo abaixo como base adicional para sua resposta:
    {snippet}
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

    return resposta, quick_replies
