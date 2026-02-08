import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from agents.tools import buscar_demandas_por_status, estatisticas_por_realizador, analisar_linha_tempo_ticket, identificar_demandas_duplicadas

load_dotenv()

def iniciar_orquestrador_gestao():
    # Usando GPT-4 pela precisão em análise de regras de negócio
    #llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    llm = ChatOllama(model="llama3.1", temperature=0)

    # Lista de ferramentas que o gestor terá à disposição
    tools = [
        buscar_demandas_por_status,
        estatisticas_por_realizador,
        analisar_linha_tempo_ticket,
        identificar_demandas_duplicadas
    ]

    # Prompt de Sistema focado em Gerenciamento de Projetos e Pipeline
    prompt_sistema = """Você é o Orquestrador de Projetos da SEMEF para o sistema CITSM.
    Sua prioridade absoluta é o gerenciamento de 'Demandas em Andamento'.
    
    Suas diretrizes de gestão são:
    1. **Prioridade Máxima**: Monitorar demandas em andamento e garantir que os 'Principais Realizadores' não estejam sobrecarregados.
    2. **Monitor de Bloqueios**: Identificar demandas 'Suspensas por falta de informação' ou 'Suspensas por Homologação/Testes'.
    3. **Qualidade**: Detectar demandas duplicadas comparando resumos e descrições.
    4. **Pipeline**: Analisar a linha do tempo para identificar tickets que não sofrem alteração há muito tempo.
    5. **Identificar e LISTAR duplicados existentes para evitar retrabalho. Ao identificar duplicatas, apresente-as em formato de lista, mostrando o 
    'Ticket Principal' e o 'Resumo' comum entre eles.
    
    Sempre que encontrar um problema (ex: técnico sobrecarregado ou ticket parado em homologação), sugira uma ação corretiva para o Gestor."""

    # Puxando o template de prompt padrão para agentes de função
    base_prompt = hub.pull("hwchase17/openai-functions-agent")

    # Adicionando o nosso contexto ao prompt base
    full_prompt = base_prompt.partial(instructions=prompt_sistema)

    # Criando o agente
    agent = create_openai_functions_agent(llm, tools, full_prompt)

    return AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    pmo_virtual = iniciar_orquestrador_gestao()

    # Exemplo de consulta de gestão
    print("🤖 Iniciando consulta de gerenciamento...")
    pmo_virtual.invoke({
        "input": "Como está a carga de trabalho atual? Existem demandas em andamento que estão paradas há muito tempo em homologação?"
    })