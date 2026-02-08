import os
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.agents.agent import AgentExecutor
from langchain.agents.react.agent import create_react_agent
from langchain.prompts import PromptTemplate
from langchain import hub

# Ajuste de Path para reconhecimento do pacote
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools import (
    listar_demandas_atuais,
    buscar_detalhes_subticket,
    estatisticas_por_realizador,
    identificar_demandas_duplicadas,
    gerar_relatorio_envelhecimento
)

load_dotenv()

def iniciar_orquestrador():
    llm = ChatOllama(model="llama3.1", temperature=0)

    tools = [
        listar_demandas_atuais,
        buscar_detalhes_subticket,
        estatisticas_por_realizador,
        identificar_demandas_duplicadas,
        gerar_relatorio_envelhecimento
    ]

    # Ajuste no template para proibir a tradução dos nomes das ferramentas
    template = """Você é o PMO Virtual da SEMEF. 
    
    REGRAS CRÍTICAS:
    - No campo 'Action', você DEVE usar EXATAMENTE o nome da função Python, sem traduzir.
    - Use apenas um dos nomes: [{tool_names}].
    - No campo 'Action Input', use apenas 'None' ou o ID solicitado.

    Ferramentas:
    {tools}

    Formato:
    Question: {input}
    Thought: [seu raciocínio]
    Action: [nome_tecnico_da_ferramenta]
    Action Input: [valor ou None]
    Observation: [resultado]
    ... (repetir se necessário)
    Thought: Eu sei a resposta final
    Final Answer: [sua resposta em português]

    {agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)
    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        # Alterado para 'force' que é o padrão mais estável para evitar erros de gerador
        early_stopping_method="force"
    )

if __name__ == "__main__":
    pmo = iniciar_orquestrador()
    print("🤖 PMO Virtual pronto. Digite 'sair' para encerrar.")

    while True:
        pergunta = input("\n📝 Digite sua consulta de gestão: ")
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            break

        try:
            pmo.invoke({"input": pergunta})
        except Exception as e:
            print(f"❌ Erro: {e}")