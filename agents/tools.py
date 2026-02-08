import os
from datetime import datetime
from pymongo import MongoClient
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

def get_collection():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client['citsm_analyzer']['ods_itsm']

@tool
def listar_demandas_atuais(observacao: str = None):
    """
    Lista as demandas em aberto ou andamento criadas a partir de 2025.
    Foca no TICKET_SUBTICKET como identificador principal.
    """
    col = get_collection()
    data_limite = datetime(2025, 1, 1)

    query = {
        "STATUS": {"$ne": "Fechado"},
        "ia_analysis_ready.dt_abertura_iso": {"$gte": data_limite}
    }

    resultados = list(col.find(query).sort("ia_analysis_ready.dt_abertura_iso", -1).limit(15))

    if not resultados:
        return "Nenhuma demanda ativa encontrada de 2025 em diante."

    return [
        {
            "subticket": r.get("TICKET_SUBTICKET"),
            "sistema": r.get("SISTEMA"),
            "status": r.get("STATUS"),
            "resumo": r.get("RESUMO_TICKET")[:80] if r.get("RESUMO_TICKET") else "Sem resumo"
        } for r in resultados
    ]

@tool
def buscar_detalhes_subticket(subticket_id: str):
    """
    Busca a descrição completa e o status de um Subticket específico através do seu ID.
    """
    col = get_collection()
    res = col.find_one({"TICKET_SUBTICKET": str(subticket_id)})

    if not res:
        return f"Subticket {subticket_id} não encontrado."

    return {
        "subticket": res.get("TICKET_SUBTICKET"),
        "descricao": res.get("DESCRICAO"),
        "status": res.get("STATUS"),
        "tecnico": res.get("TECNICORESPONSAVEL"),
        "abertura": res.get("ia_analysis_ready", {}).get("dt_abertura_iso")
    }

@tool
def estatisticas_por_realizador(dummy: str = None):
    """
    Retorna o ranking de técnicos (TECNICORESPONSAVEL) com mais demandas em aberto em 2025/2026.
    """
    col = get_collection()
    data_limite = datetime(2025, 1, 1)

    pipeline = [
        {"$match": {
            "STATUS": {"$ne": "Fechado"},
            "ia_analysis_ready.dt_abertura_iso": {"$gte": data_limite}
        }},
        {"$group": {"_id": "$TECNICORESPONSAVEL", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    return list(col.aggregate(pipeline))

@tool
def identificar_demandas_duplicadas(termo: str = None):
    """
    Analisa a base de dados em busca de subtickets com resumos muito similares que podem ser duplicatas.
    """
    col = get_collection()
    pipeline = [
        {"$match": {"STATUS": {"$ne": "Fechado"}}},
        {"$group": {
            "_id": "$RESUMO_TICKET",
            "ocorrencias": {"$sum": 1},
            "subtickets": {"$push": "$TICKET_SUBTICKET"}
        }},
        {"$match": {"ocorrencias": {"$gt": 1}}},
        {"$limit": 5}
    ]
    return list(col.aggregate(pipeline))

@tool
def gerar_relatorio_envelhecimento(dias_minimos: int = 10):
    """
    Calcula há quantos dias as demandas de 2025/2026 estão abertas e não finalizadas.
    Retorna os subtickets que excederam o limite de dias informado (padrão 10 dias).
    """
    col = get_collection()
    hoje = datetime.utcnow()
    data_limite = datetime(2025, 1, 1)

    pipeline = [
        # Filtro inicial: Apenas 2025+, Status não finalizado e que tenha data ISO
        {"$match": {
            "STATUS": {"$ne": "Fechado"},
            "ia_analysis_ready.dt_abertura_iso": {"$gte": data_limite}
        }},
        # Cálculo da diferença de dias
        {"$addFields": {
            "dias_de_vida": {
                "$dateDiff": {
                    "startDate": "$ia_analysis_ready.dt_abertura_iso",
                    "endDate": hoje,
                    "unit": "day"
                }
            }
        }},
        # Filtro de envelhecimento
        {"$match": {"dias_de_vida": {"$gte": dias_minimos}}},
        # Projeção do que é importante para o gestor
        {"$project": {
            "subticket": "$TICKET_SUBTICKET",
            "sistema": "$SISTEMA",
            "status": "$STATUS",
            "tecnico": "$TECNICORESPONSAVEL",
            "dias_aberto": "$dias_de_vida"
        }},
        {"$sort": {"dias_aberto": -1}}
    ]

    resultados = list(col.aggregate(pipeline))

    if not resultados:
        return f"Nenhuma demanda ativa com mais de {dias_minimos} dias de atraso."

    return resultados

