import os
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.agents.agent import AgentExecutor
from langchain.agents.react.agent import create_react_agent
from langchain.prompts import PromptTemplate

# Garante que o pacote 'agents' seja reconhecido
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.tools import (
    listar_demandas_atuais,
    buscar_detalhes_subticket,
    estatisticas_por_realizador,
    executar_diagnostico_pmo_real,
    gerar_relatorio_envelhecimento,
    busca_avancada_texto
)

load_dotenv()

def iniciar_orquestrador():
    llm = ChatOllama(
        model="llama3.1",
        temperature=0,
        stop=["Observation:", "Observation", "\nObservation:"] # Força a parada para o sistema injetar o dado real
    )

    tools = [
        listar_demandas_atuais,
        buscar_detalhes_subticket,
        estatisticas_por_realizador,
        executar_diagnostico_pmo_real,
        gerar_relatorio_envelhecimento,
        busca_avancada_texto
    ]

    # ... (mantenha os imports)

    template = """Você é o PMO Virtual da SEMEF. 
    Responda apenas com base nos dados retornados pelas ferramentas.

    Nomes das ferramentas: {tool_names}
    Descrições: {tools}

    Siga este formato estritamente:
    Question: a pergunta do usuário
    Thought: descreva em uma frase o que você vai buscar.
    Action: o nome da ferramenta (deve ser um de [{tool_names}])
    Action Input: o parâmetro ou None
    Observation: o resultado da ferramenta
    ... (repetir se necessário)
    Thought: Agora eu tenho a resposta.
    Final Answer: o relatório final em português.

    Question: {input}
    Thought: {agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)
    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3, # Reduzido para evitar loops longos
        early_stopping_method="force"
    )

if __name__ == "__main__":
    pmo = iniciar_orquestrador()
    print("🚀 PMO Virtual SEMEF Ativo. Digite 'sair' para encerrar.")

    while True:
        pergunta = input("\n📝 Consulta: ")
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            break
        try:
            pmo.invoke({"input": pergunta})
        except Exception as e:
            print(f"❌ Erro: {e}")