from agents.orchestrator import iniciar_orquestrador

pmo = iniciar_orquestrador()
pergunta = (
    "rode a ferramenta executar_diagnostico_pmo_real e me diga os IDs dos tickets que ela retornar."
)

pmo.invoke({"input": pergunta})