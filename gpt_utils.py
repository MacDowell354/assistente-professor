import os
import re
import random
from openai import OpenAI, OpenAIError

# Configurar seu arquivo de transcrições
TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), "transcricoes.txt")

# Instância do cliente OpenAI
client = OpenAI()

# Mensagem padrão para temas não encontrados
OUT_OF_SCOPE_MSG = (
    "Desculpe, ainda não tenho informações suficientes sobre esse tema específico do curso. "
    "Por favor, envie outra pergunta ou consulte o material da aula."
)

# Saudações e fechamentos para humanizar as respostas
GREETINGS = [
    "Olá, querido aluno",
    "Oi, tudo bem?",
    "Bem-vindo(a) de volta!",
    "Olá, estou aqui para ajudar"
]

CLOSINGS = [
    "Fique à vontade para perguntar sempre que quiser evoluir.",
    "Espero ter ajudado! Qualquer dúvida, é só chamar.",
    "Conte comigo para o seu sucesso no Consultório High Ticket."
]

def normalize_text(text):
    """Normaliza texto para melhorar buscas: minusculas, sem acentos, sem caracteres especiais."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def search_transcripts_by_theme(theme):
    """
    Busca no arquivo de transcrições o trecho que contém o tema.
    Retorna um trecho do texto relevante para o tema.
    """
    theme_norm = normalize_text(theme)
    if not os.path.exists(TRANSCRIPTS_PATH):
        return None

    with open(TRANSCRIPTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content_norm = normalize_text(content)

    # Buscar o tema no conteúdo
    pos = content_norm.find(theme_norm)
    if pos == -1:
        # Se não encontrar exato, tentar buscar por palavras-chave (simplificação)
        palavras = theme_norm.split()
        for palavra in palavras:
            pos = content_norm.find(palavra)
            if pos != -1:
                break
        else:
            return None  # Não encontrou nada

    # Retorna trecho +/- 500 caracteres antes e depois do termo encontrado para contexto
    start = max(0, pos - 500)
    end = min(len(content), pos + 500)
    snippet = content[start:end]

    return snippet.strip()

def generate_answer(question, context="", history=None, tipo_de_prompt=None, is_first_question=True):
    """
    Gera resposta didática e objetiva para pergunta, buscando conteúdo no arquivo de transcrições.
    Usa GPT-4 com fallback para GPT-3.5.
    """

    saudacao = random.choice(GREETINGS) if is_first_question else ""
    fechamento = random.choice(CLOSINGS)

    snippet = search_transcripts_by_theme(question)

    if snippet:
        prompt = (
            "Você é Nanda Mac.ia, professora do curso Consultório High Ticket. "
            "Explique com suas próprias palavras, de forma humana, didática e acolhedora o tema abaixo, exatamente como ensinaria numa aula particular ao aluno do curso. "
            "Use SOMENTE as informações do conteúdo fornecido, seja direta e utilize exemplos práticos e simples para aplicação no dia a dia do consultório. "
            "Não mencione a palavra 'trecho' ou que está respondendo com base em um texto específico, responda naturalmente como uma professora dedicada explicando diretamente ao aluno. "
            "\n\nConteúdo da aula:\n" + snippet + "\n\n"
            "[IMPORTANTE] Seja objetiva, acolhedora e didática respondendo APENAS sobre o tema indicado."
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
            # Fallback para GPT-3.5
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
        if saudacao:
            return f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"
        else:
            return f"{explicacao}<br><br>{fechamento}"

    else:
        # Quando não tem conteúdo relevante
        if saudacao:
            return f"{saudacao}<br><br>{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"
        else:
            return f"{OUT_OF_SCOPE_MSG}<br><br>{fechamento}"

# Se desejar, pode incluir testes unitários aqui, mas geralmente esses arquivos não os incluem.
