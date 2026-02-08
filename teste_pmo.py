from agents.orchestrator import iniciar_orquestrador

pmo = iniciar_orquestrador()
pergunta = (
    "Faça um diagnóstico do pipeline atual: quais as 5 demandas mais antigas em andamento, "
    "quem são os técnicos responsáveis por elas e existem subtickets duplicados que podem ser unificados?"
)

pmo.invoke({"input": pergunta})