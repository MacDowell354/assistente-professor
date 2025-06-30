import os
import unicodedata
import re

OUT_OF_SCOPE_MSG = (
    "Sua pergunta demonstra interesse e vontade de aprender!<br>"
    "No entanto, esse tema ainda não faz parte do conteúdo oficial do curso <b>Consultório High Ticket</b>.<br>"
    "Recomendo focar nas estratégias, conceitos e práticas ensinadas nas aulas para transformar seu consultório.<br>"
    "Sua dúvida será encaminhada à equipe pedagógica para avaliarmos uma possível inclusão em futuras atualizações.<br>"
    "Continue participando!"
)

def normalize_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text)
    ascii_only = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

CANONICAL_QA = {
    "explique em passos claros o conceito de posicionamento de alto valor ensinado no curso":
        "<b>O conceito de posicionamento de alto valor no curso Consultório High Ticket envolve:</b><br><br>"
        "1. <b>Mentalidade protagonista:</b> Valorize sua história e seu diferencial, sem se comparar.<br>"
        "2. <b>Comunicação clara:</b> Fale com o paciente de forma simples, mostrando impacto real.<br>"
        "3. <b>Experiência diferenciada:</b> Encante o paciente em cada etapa do atendimento.<br>"
        "4. <b>Autoridade:</b> Oriente e lidere com confiança e ética.<br>"
        "5. <b>Valorização:</b> Explique suas condutas e mostre que investir em saúde é prioridade.<br><br>"
        "<b>Resultado:</b> Você é visto como referência, atrai pacientes de valor e constrói uma agenda cheia de qualidade.",

    "quais são as principais dúvidas que alunos normalmente têm sobre captação de pacientes sem usar redes sociais":
        "<b>Principais dúvidas dos alunos sobre captação sem redes sociais:</b><br><br>"
        "• Se é possível dobrar o faturamento sem Instagram ou anúncios.<br>"
        "• Como criar indicações orgânicas e conseguir pacientes high ticket offline.<br>"
        "• Como transformar atendimento e experiência do paciente em fonte de novas indicações.<br>"
        "• Como lidar com concorrência em cidades pequenas.<br>"
        "• Se é preciso investir em brindes, eventos ou ações complexas.<br>"
        "• Como adaptar o método para cada especialidade.<br>"
        "• Como estruturar um processo para manter a agenda cheia sem depender só do boca a boca.",

    "faça uma revisão rápida dos pontos centrais do método de precificação estratégica":
        "<b>Revisão dos pontos centrais do método de precificação estratégica:</b><br><br>"
        "1. <b>Mude sua mentalidade:</b> Valorize o seu trabalho.<br>"
        "2. <b>Baseie-se no resultado:</b> O valor é o resultado que você gera, não o preço do colega.<br>"
        "3. <b>Apresente com clareza:</b> Mostre benefícios e diferenciais do serviço.<br>"
        "4. <b>Mantenha coerência e ética:</b> Saiba recusar pacientes fora do seu perfil.<br>"
        "5. <b>Use o timing certo:</b> Apresente o valor de forma natural, como parte do plano.<br><br>"
        "<b>Assim você dobra o faturamento com posicionamento e valorização profissional.</b>",

    "como aplico o roteiro de atendimento high ticket na primeira consulta com um paciente novo":
        "<b>Passo a passo do roteiro de atendimento High Ticket:</b><br><br>"
        "1. <b>Recepção acolhedora:</b> Chame o paciente pelo nome, demonstre interesse genuíno.<br>"
        "2. <b>Escuta ativa:</b> Ouça atentamente e valide as necessidades do paciente.<br>"
        "3. <b>Apresente o plano:</b> Explique diagnóstico e ação de forma simples.<br>"
        "4. <b>Mostre autoridade:</b> Oriente o melhor caminho com segurança.<br>"
        "5. <b>Use gatilhos do método:</b> Conte histórias e foque na especificidade.<br>"
        "6. <b>Apresente o valor:</b> Mostre o investimento como parte do sucesso.<br>"
        "7. <b>Finalize com orientação clara e pós-atendimento.</b>",

    "eu só levantaria preço com o cliente na segunda sessão está certo isso":
        "<b>Correção importante:</b><br><br>"
        "Não está certo!<br>"
        "Pelo método Consultório High Ticket, o valor do seu trabalho deve ser apresentado já na <b>primeira consulta</b>, com naturalidade e clareza.<br>"
        "Adiar a conversa sobre valores pode passar insegurança ao paciente. Mostre que o investimento faz parte do plano de cuidado e atraia pacientes que valorizam seu método, evitando perda de tempo com quem não é o perfil ideal.",

    "me mostre uma estratégia offline para atrair pacientes de alto valor sem usar instagram ou anúncios":
        "<b>Estratégias offline para atrair pacientes high ticket:</b><br><br>"
        "• Encante o paciente desde o primeiro contato, criando uma experiência única.<br>"
        "• Use o pós-atendimento para fortalecer o vínculo.<br>"
        "• Construa uma rede de indicações com outros profissionais de saúde.<br>"
        "• Utilize detalhes pessoais do paciente para surpreender positivamente.<br>"
        "• Surpreenda com atenção genuína e acompanhamento.<br><br>"
        "<b>Essas ações geram indicações espontâneas e lotam sua agenda sem redes sociais.</b>",

    "como estruturo a apresentação do valor do health plan para que o paciente veja o retorno do investimento":
        "<b>Como apresentar o valor do Health Plan:</b><br><br>"
        "1. Explique que o plano foi criado para facilitar a vida do paciente, trazendo clareza.<br>"
        "2. Mostre benefícios: acompanhamento, resultados esperados e previsibilidade.<br>"
        "3. Associe valor ao resultado: use exemplos e conquistas reais.<br>"
        "4. Apresente etapas e vantagens do acompanhamento contínuo.<br>"
        "5. Apresente o investimento como parte natural do cuidado, sem justificativas.<br>"
        "6. Finalize mostrando como investir em saúde é um ganho a longo prazo.",

    "me ajude a montar um health plan para um paciente com enxaqueca crônica":
        "<b>Health Plan para enxaqueca crônica:</b><br><br>"
        "1. <b>Anamnese detalhada:</b> Identifique gatilhos, hábitos e histórico.<br>"
        "2. <b>Educação:</b> Explique o diagnóstico de forma simples.<br>"
        "3. <b>Plano de ação:</b> Inclua orientações clínicas, alimentares, rotina de sono e técnicas para estresse.<br>"
        "4. <b>Acompanhamento:</b> Agende retornos e acompanhe o progresso.<br>"
        "5. <b>Apresentação do investimento:</b> Mostre o valor como parte do processo para reduzir crises e melhorar a qualidade de vida do paciente.",

    "quais exercícios devo fazer para melhorar minhas costas em casa":
        "Sua pergunta demonstra interesse, mas esse tema não faz parte do conteúdo do curso <b>Consultório High Ticket</b>.<br>"
        "Nosso foco é ajudar você a dobrar o faturamento do consultório com estratégias de posicionamento, valorização e captação de pacientes high ticket.<br>"
        "Para recomendações de exercícios físicos, oriento buscar um profissional da área de saúde física ou fisioterapia."
}

CANONICAL_QA_NORMALIZED = {normalize_key(k): v for k, v in CANONICAL_QA.items()}

def generate_answer(
    question: str,
    context: str = "",
    history: str = None,
    tipo_de_prompt: str = None
) -> str:
    key = normalize_key(question)
    if key in CANONICAL_QA_NORMALIZED:
        return CANONICAL_QA_NORMALIZED[key]
    if context and len(context.strip()) > 20:
        return context.strip()
    return OUT_OF_SCOPE_MSG
