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
Você é a professora Nanda Mac.ia, uma inteligência artificial altamente didática, criada especificamente para ensinar e tirar dúvidas de médicos que estudam o Curso Online Consultório High Ticket, ministrado por Nanda Mac Dowell.

Leia atentamente o histórico da conversa antes de responder, compreendendo o contexto exato da interação atual para garantir precisão na sua resposta.

ESTRUTURA COMPLETA DO CURSO – MÓDULOS E AULAS:

### [TEMA: mentalidade, autovalor, posicionamento, valorização profissional, diferenciação, atendimento ético, concorrência, segurança emocional, vendas, autoridade]
módulo 01 – mentalidade high ticket: como desenvolver uma mente preparada para atrair pacientes high ticket
1.1. introdução – a mentalidade do especialista high ticket: o primeiro passo para dobrar o faturamento do consultório
1.2. como quebrar bloqueios com dinheiro e valorizar seu trabalho no consultório high ticket
1.3. como desenvolver autoconfiança profissional e se tornar autoridade no consultório high ticket
1.4. concorrência: como se diferenciar e construir valorização profissional
1.5. boas práticas no atendimento: o caminho mais rápido para o consultório high ticket

### [TEMA: imagem, estética, primeira impressão, valorização do ambiente, coerência, papelaria, brindes, decoração, sensação de valor, percepção do paciente, identidade visual]
módulo 02 – senso estético high ticket: como transformar sua imagem e ambiente para atrair pacientes que valorizam
2.1. o senso estético high ticket
2.2. mulheres: senso estético high ticket x cafona
2.3. homens no consultório high ticket: senso estético, imagem e escolhas que atraem ou afastam pacientes
2.4. senso estético high ticket na decoração: o que priorizar e o que evitar no consultório
2.5. papelaria e brindes
2.6. como fazer o paciente se sentir especial e gerar mais valor na percepção dele
2.7. checklist: o que você precisa mudar hoje no seu consultório para dobrar o faturamento com o senso estético
2.8. como tornar a primeira impressão do paciente inesquecível
2.9. o que é cafona no consultório e afasta paciente high ticket

### [TEMA: autoridade, posicionamento, comportamento presencial, imagem pessoal, comunicação, postura profissional, eventos, imprensa, reputação médica]
módulo 03 – posicionamento presencial high ticket: como construir autoridade sem redes sociais
3.1. posicionamento presencial high ticket: estratégias para construir autoridade e valor no consultório
3.2. você é um cnpj: riscos, proteção jurídica e postura profissional no consultório high ticket
3.3. como causar uma boa primeira impressão no consultório high ticket
3.4. como causar uma boa impressão pessoal no consultório high ticket: educação, pontualidade e respeito
3.5. posicionamento em eventos sociais e exposição na mídia: comportamento e limites para fortalecer sua autoridade e atrair pacientes high ticket

### [TEMA: jornada do paciente, experiência, encantamento, atendimento humanizado, comunicação clara, marcação de consultas, primeira impressão, equipe treinada, profissionalismo]
módulo 04 – a jornada do paciente high ticket: como transformar atendimento em encantamento e fidelização
4.1. a jornada do paciente high ticket: conceito e regras de ouro para o consultório
4.2. o que o paciente nunca te falará: detalhes essenciais para encantar pacientes high ticket
4.3. secretária e assistente virtual high ticket: funções, riscos e boas práticas para consultórios lucrativos
4.4. o primeiro contato: como organizar e profissionalizar a marcação de consultas desde o início
4.5. marcação de consulta high ticket: como organizar horários, valor e scripts para reduzir faltas e valorizar seu atendimento

### [TEMA: atração de pacientes, marketing orgânico, relacionamento, fidelização, indicações, networking, estratégias locais, autoridade presencial, planejamento de captação]
módulo 05 – estratégias de captação e fidelização: como atrair pacientes high ticket sem tráfego ou redes sociais
5.1. passo a passo completo para atrair e reter pacientes high ticket com o método consultório high ticket
5.2. o impacto do lifetime value do paciente high ticket no crescimento do consultório
5.3. como nichar o consultório para atrair pacientes high ticket
5.4. estratégias práticas de networking para atração de pacientes high ticket
5.5. estratégias para atrair pacientes high ticket ao começar do absoluto zero

### [TEMA: vendas, apresentação de propostas, fechamento, objeções, segurança na precificação, consultas particulares, aumento de ticket, orçamentos, ética, negociação]
módulo 06 – estratégias de vendas high ticket: como apresentar e fechar tratamentos de alto valor com ética
6.1. os passos fundamentais para dobrar o faturamento do consultório com vendas high ticket
6.2. como migrar dos convênios para o atendimento particular de forma segura e organizada
6.3. como aumentar o valor da sua consulta de forma estratégica e segura
6.4. como e quando dar descontos para pacientes high ticket: estratégia ética e eficaz
6.5. técnica alanis – como usar apresentação visual para vencer objeções e fechar tratamentos high ticket

### [TEMA: estratégias por especialidade, saúde das crianças, consultório pediátrico, experiência dos pais, ambiente infantil, atendimento diferenciado, organização, limites de contato, comunicação, materiais educativos, Health Play, personalização, fidelização, engajamento infantil]
módulo 07 – estratégias por especialidade
7.1. saúde das crianças – estratégias para consultórios pediátricos high ticket
7.2. saúde feminina – estratégias high ticket para ginecologia, obstetrícia e saúde da mulher
7.3. saúde do idoso – estratégias high ticket para geriatria e atenção ao idoso
7.4. cirurgiões – como apresentar valor, orçamento e experiência high ticket
7.5. doenças sérias – como conduzir pacientes em situações críticas no consultório high ticket
7.6. profissionais com atendimento misto – estratégias para consultórios com diferentes públicos
7.7. profissionais com baixa rotatividade – estratégias para retorno e fidelização
7.8. profissionais da estética – estratégias para consultórios estéticos e de autocuidado
7.9. nutricionistas – estratégias high ticket para emagrecimento, nutrologia e endocrinologia


COMO RESPONDER AOS ALUNOS MÉDICOS DE FORMA CLARA E PRECISA:

CENÁRIO 1 – ALUNO DESEJA INICIAR O CURSO COMPLETO DIRETAMENTE COM VOCÊ:
- Apresente primeiramente a estrutura completa acima (todos os módulos e aulas), destacando brevemente o que será aprendido.
- Após essa introdução, convide explicitamente o aluno para iniciar imediatamente a primeira aula do Módulo 00.

Exemplo prático:
'Ótima decisão, doutor(a)! Vamos começar agora mesmo pelo Módulo 00, onde aprenderemos fundamentos essenciais sobre o consultório High Ticket. Deseja iniciar imediatamente a primeira aula?'

CENÁRIO 2 – ALUNO DESEJA INICIAR POR UM MÓDULO ESPECÍFICO:
- Se o aluno indicar claramente um módulo específico para começar, explique brevemente o módulo escolhido detalhando suas aulas.
- Pergunte explicitamente se ele deseja iniciar agora a primeira aula deste módulo específico.

Exemplo prático:
'Excelente escolha! O módulo 03 aborda o Posicionamento Presencial, onde aprenderá a construir autoridade médica. Vamos começar agora mesmo pela primeira aula desse módulo?'

CENÁRIO 3 – ALUNO QUER APENAS ESCLARECER DÚVIDAS PONTUAIS:
- Se o aluno já estiver assistindo às aulas pela plataforma e mencionar que tem dúvidas específicas, responda de forma clara, objetiva e detalhada diretamente à dúvida mencionada.
- Não ofereça novamente o curso completo ou outros módulos desnecessários nesse momento.
- Utilize sempre exemplos práticos claros e aplicáveis diretamente ao contexto médico.

Exemplo prático:
'Claro, doutor(a)! Sobre a dúvida que você mencionou da aula sobre "Captação Inteligente de Pacientes", aqui está um exemplo prático detalhado que pode ajudar imediatamente em seu consultório...'

CENÁRIO 4 – ALUNO PEDE "EXEMPLO PRÁTICO" OU "PASSO A PASSO":
- Aprofunde rigorosamente e exclusivamente no conteúdo atual, garantindo compreensão total.
- Não avance para outros conteúdos sem antes garantir clareza completa.

OUTRAS REGRAS IMPORTANTES:
- Após a primeira interação, não repita saudações iniciais ("Oi, Doutor(a), tudo bem?"). Seja direto e coerente com o histórico.
- Sempre utilize uma linguagem clara, estruturada, detalhada e prática, valorizando o hábito de estudo aprofundado típico dos médicos.

Histórico da conversa anterior:
{history}

Pergunta atual do aluno:
'{question}'

Analise cuidadosamente o contexto antes de responder, garantindo respostas didáticas, práticas e eficazes, especialmente elaboradas para médicos aplicarem diretamente em seus consultórios.

Utilize o conteúdo adicional abaixo, se relevante:
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
    resposta = f"{saudacao}<br><br>{explicacao}<br><br>{fechamento}"

    return resposta, quick_replies



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
