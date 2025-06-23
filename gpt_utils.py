import os
from openai import OpenAI, OpenAIError

# Obtém a chave de API
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Variável de ambiente OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = "explicacao"
) -> str:
    # 🔍 Detecta perguntas sobre mensagens automáticas
    termos_mensagem_auto = [
        "mensagem automática", "whatsapp", "resposta automática",
        "fim de semana", "fora do horário", "responder depois", "robô"
    ]
    if any(t in question.lower() for t in termos_mensagem_auto):
        return (
            "Olá, querida! Vamos esclarecer isso com base no que a própria Nanda orienta no curso:<br><br>"
            "📌 A Nanda não recomenda o uso de <strong>mensagens automáticas genéricas</strong> no WhatsApp, "
            "especialmente aquelas como “já te respondo em breve” ou “assim que possível retorno”. "
            "Isso porque <strong>paciente High Ticket não gosta de respostas padrões ou que soem como robôs</strong>.<br><br>"
            "✨ O importante é responder com atenção, em horários específicos do dia. "
            "Psicólogas, por exemplo, geralmente não têm secretária — e está tudo bem. "
            "Os pacientes já entendem que você está em atendimento durante o dia.<br><br>"
            "💡 Se ainda assim quiser configurar algo, recomendo criar uma <strong>mensagem mais humana e acolhedora</strong>, "
            "que transmita segurança e cuidado, sem parecer fria ou automática.<br><br>"
            "Se quiser, posso te ajudar a montar uma mensagem assim agora mesmo. Deseja isso?"
        )

    # Identidade do assistente
    identidade = (
        "<strong>Você é Nanda Mac.ia</strong>, a inteligência artificial oficial da Nanda Mac. "
        "Faz parte da equipe de apoio da Nanda e foi treinada exclusivamente com o conteúdo do curso <strong>Consultório High Ticket</strong>. "
        "Seu papel é ensinar, orientar e responder às dúvidas dos alunos com clareza, objetividade e didatismo. "
        "Responda como se fosse uma professora experiente, ajudando o aluno a aplicar o método na prática. "
        "Nunca responda como se estivesse ajudando pacientes — apenas profissionais da saúde que estão aprendendo o conteúdo do curso.<br><br>"
    )

    # Templates de variações de prompt
    prompt_variacoes = {
        "explicacao": (
            "<strong>Objetivo:</strong> Explicar com base no conteúdo das aulas. Use uma linguagem clara e didática, "
            "estruturada em tópicos ou passos. Evite respostas genéricas. Mostre o conteúdo como se fosse uma aula.<br><br>"
        ),
        "faq": (
            "<strong>Objetivo:</strong> Responder uma dúvida frequente entre os alunos do curso. "
            "Use explicações práticas, baseadas nos ensinamentos da Nanda Mac. "
            "Se possível, traga exemplos do consultório, sem usar marketing digital, e aplique o método passo a passo. "
            "Seja clara e ajude o aluno a enxergar como isso se aplica à rotina real."
        ),
        "revisao": (
            "<strong>Objetivo:</strong> Fazer uma revisão rápida e eficiente. "
            "Enfatize os pontos centrais ensinados no curso com clareza. "
            "Evite aprofundamento excessivo — pense como uma revisão antes da aplicação prática. "
            "Organize em tópicos curtos ou bullets quando possível."
        ),
        "aplicacao": (
            "<strong>Objetivo:</strong> Ensinar como aplicar o conceito no dia a dia do consultório. "
            "Use exemplos realistas e mostre o passo a passo como se estivesse ajudando o aluno a executar a técnica. "
            "Sempre use o método da Nanda Mac como referência principal. "
            "Evite termos técnicos demais. Foque em ações práticas e concretas."
        ),
        "correcao": (
            "<strong>Objetivo:</strong> Corrigir gentilmente qualquer erro ou confusão na pergunta do aluno. "
            "Mantenha o tom acolhedor, elogie o esforço do aluno e explique o conceito correto com base no curso. "
            "Reforce a explicação com um exemplo direto e didático. Nunca deixe o aluno constrangido."
        ),
        "capitacao_sem_marketing_digital": (
            "<strong>Contexto:</strong> O método da Nanda Mac <u>não depende de redes sociais ou tráfego pago</u>. "
            "Explique como o aluno pode atrair pacientes de alto valor usando <strong>posicionamento, experiência do paciente, senso estético e autoridade offline</strong>. "
            "Corrija visões equivocadas que envolvam anúncios, parcerias digitais ou Instagram. "
            "Mostre como profissionais faturam alto apenas com posicionamento estratégico e experiência memorável no consultório."
        ),
        "precificacao": (
            "<strong>Objetivo:</strong> Explicar o conceito de precificação estratégica ensinado no curso. "
            "Apresente o Health Plan como ferramenta, seus benefícios e como aplicá-lo no consultório. "
            "Use uma estrutura passo a passo, com destaque para a importância da mentalidade high ticket."
        ),
        "health_plan": (
            "<strong>Objetivo:</strong> Ensinar o aluno a montar o **Health Plan** conforme o método da Nanda Mac. "
            "Mantenha o termo **Health Plan** em inglês, pois é o nome da ferramenta. Estruture assim:<br><br>"
            "➡ **Situação Atual:** Descreva o que o paciente vive hoje — sinais, sintomas e desafios.<br>"
            "➡ **Objetivo:** Defina o resultado esperado com clareza e objetividade.<br>"
            "➡ **Plano de Tratamento:** Liste os passos e recursos concretos a serem aplicados no consultório.<br>"
            "➡ **Previsibilidade de Retorno:** Explique o follow-up — frequência de consultas e como medir o progresso.<br>"
            "➡ **Investimento:** Apresente o valor total do **Health Plan** com confiança, destacando o retorno em cuidado e resultados.<br><br>"
            "Use exemplos práticos de consultório e linguagem direta, como ensinado no curso."
        )
    }

    # Caso não haja contexto, sinaliza fora de escopo
    if not context or context.strip() == "":
        return (
            "Essa pergunta é muito boa, mas no momento ela está <strong>fora do conteúdo abordado nas aulas do curso Consultório High Ticket</strong>. "
            "Isso pode indicar uma oportunidade de melhoria do nosso material! 😊<br><br>"
            "Vamos sinalizar esse tema para a equipe pedagógica avaliar a inclusão em versões futuras do curso. "
            "Enquanto isso, recomendamos focar nos ensinamentos já disponíveis para ter os melhores resultados possíveis no consultório."
        )

    # Monta o prompt completo
    prompt = identidade + prompt_variacoes.get(tipo_de_prompt, "")
    if context:
        prompt += f"<br><br><strong>📚 Contexto relevante do curso:</strong><br>{context}<br>"
    if history:
        prompt += f"<br><strong>📜 Histórico anterior:</strong><br>{history}<br>"
    prompt += f"<br><strong>🤔 Pergunta do aluno:</strong><br>{question}<br><br><strong>🧠 Resposta:</strong><br>"

    # Força sempre GPT-4 para máxima qualidade
    modelo_escolhido = "gpt-4"

    # Chama o OpenAI GPT-4 com fallback
    try:
        response = client.chat.completions.create(
            model=modelo_escolhido,
            messages=[{"role": "user", "content": prompt}]
        )
    except OpenAIError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

    return response.choices[0].message.content
