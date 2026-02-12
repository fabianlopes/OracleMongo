import os
from datetime import datetime
from pymongo import MongoClient
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

import dns.resolver

def get_collection():
    # Força um tempo de resposta menor para o DNS não travar o Agente
    client = MongoClient(
        os.getenv("MONGO_URI"),
        serverSelectionTimeoutMS=5000, # 5 segundos de limite para achar o servidor
        connectTimeoutMS=5000
    )
    return client['citsm_analyzer']['ods_itsm']

@tool
def executar_diagnostico_pmo_real(dummy: str = None):
    """Executa a pipeline de agregação focando apenas em demandas ATIVAS."""
    col = get_collection()
    pipeline = [
        # FILTRO CRÍTICO: Remove o que já foi cancelado ou fechado
        {"$match": {"STATUS": {"$nin": ["Cancelado", "Fechado", "Concluído"]}}},
        {"$facet": {
            "mais_antigos": [
                {"$sort": {"DTABERTURA": 1}},
                {"$limit": 5},
                {"$project": {"TICKET": "$TICKET_SUBTICKET", "TECNICO": "$TECNICORESPONSAVEL", "DATA": "$DTABERTURA", "STATUS": 1}}
            ],
            "duplicados": [
                {"$match": {"RESUMO_TICKET": {"$ne": None}}}, # Ignora resumos nulos
                {"$group": {"_id": "$RESUMO_TICKET", "qtd": {"$sum": 1}, "ids": {"$push": "$TICKET_SUBTICKET"}}},
                {"$match": {"qtd": {"$gt": 1}}},
                {"$sort": {"qtd": -1}},
                {"$limit": 5}
            ]
        }}
    ]
    res = list(col.aggregate(pipeline))[0]
    return f"DADOS REAIS (FILTRADOS POR ATIVOS): {str(res)}"

@tool
def busca_avancada_texto(termo: str):
    """
    Realiza uma busca por texto nos campos RESUMO_TICKET e SISTEMA.
    Útil para encontrar dados reais sobre um assunto específico.
    """
    col = get_collection()
    query = {
        "$or": [
            {"RESUMO_TICKET": {"$regex": termo, "$options": "i"}},
            {"SISTEMA": {"$regex": termo, "$options": "i"}}
        ],
        "ia_analysis_ready.dt_abertura_iso": {"$gte": datetime(2025, 1, 1)}
    }
    return list(col.find(query).limit(20))

@tool
def listar_demandas_atuais(observacao: str = None):
    """Lista demandas em aberto criadas a partir de 2025."""
    col = get_collection()
    query = {"STATUS": {"$ne": "Fechado"}, "ia_analysis_ready.dt_abertura_iso": {"$gte": datetime(2025, 1, 1)}}
    return list(col.find(query).sort("ia_analysis_ready.dt_abertura_iso", -1).limit(15))

@tool
def buscar_detalhes_subticket(subticket_id: str):
    """Busca detalhes de um Subticket específico pelo ID."""
    col = get_collection()
    return col.find_one({"TICKET_SUBTICKET": str(subticket_id)})

@tool
def estatisticas_por_realizador(dummy: str = None):
    """Ranking de técnicos com mais demandas em aberto em 2025/2026."""
    col = get_collection()
    pipeline = [
        {"$match": {"STATUS": {"$ne": "Fechado"}, "ia_analysis_ready.dt_abertura_iso": {"$gte": datetime(2025, 1, 1)}}},
        {"$group": {"_id": "$TECNICORESPONSAVEL", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    return list(col.aggregate(pipeline))

@tool
def gerar_relatorio_envelhecimento(dias_minimos: int = 10):
    """Calcula o aging das demandas não finalizadas de 2025/2026."""
    col = get_collection()
    pipeline = [
        {"$match": {"STATUS": {"$ne": "Fechado"}, "ia_analysis_ready.dt_abertura_iso": {"$gte": datetime(2025, 1, 1)}}},
        {"$addFields": {"dias_de_vida": {"$dateDiff": {"startDate": "$ia_analysis_ready.dt_abertura_iso", "endDate": datetime.utcnow(), "unit": "day"}}}},
        {"$match": {"dias_de_vida": {"$gte": dias_minimos}}},
        {"$sort": {"dias_de_vida": -1}}
    ]
    return list(col.aggregate(pipeline))