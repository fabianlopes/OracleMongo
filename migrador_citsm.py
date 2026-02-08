import os
import oracledb
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Carrega as credenciais do seu arquivo .env
load_dotenv()

def tratar_data(data_str):
    """
    Tenta converter as strings de data do Oracle para objetos datetime do MongoDB.
    Isso permitirá que seus agentes de IA façam análises temporais precisas.
    """
    if not data_str or data_str == 'None': return None

    # Formatos comuns encontrados em cubos de BI e ODS
    formatos = ["%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]

    for fmt in formatos:
        try:
            return datetime.strptime(str(data_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None

def migrar_para_citsm():
    # Configuração das Conexões
    try:
        ora_conn = oracledb.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASS"),
            dsn=os.getenv("ORACLE_DSN")
        )

        mongo_client = MongoClient(os.getenv("MONGO_URI"))
        # Nome do banco atualizado conforme sua solicitação
        db = mongo_client['citsm_analyzer']
        collection = db['ods_itsm']

        with ora_conn.cursor() as cursor:
            print("📡 Extraindo dados da tabela DWITSM.ODS_ITSM...")
            cursor.execute("SELECT * FROM DWITSM.ODS_ITSM")

            # Recupera os nomes das colunas dinamicamente do cursor
            colunas = [col[0] for col in cursor.description]

            count = 0
            while True:
                rows = cursor.fetchmany(1000) # Processamento em lotes (batch)
                if not rows:
                    break

                documentos = []
                for row in rows:
                    # Mapeia todas as colunas originais do DDL
                    doc = dict(zip(colunas, row))

                    # Enriquecimento de metadados para os Agentes Autônomos
                    doc['ia_analysis_ready'] = {
                        'dt_abertura_iso': tratar_data(doc.get('DTABERTURA')),
                        'dt_fim_iso': tratar_data(doc.get('DTFIM')),
                        'dt_modificacao_iso': tratar_data(doc.get('DTULTIMAMODIFICACAO')),
                        'timestamp_migracao': datetime.utcnow()
                    }

                    # Limpeza de espaços em branco (Trim) em campos de texto
                    for campo in ['RESUMO_TICKET', 'DESCRICAO', 'SISTEMA', 'STATUS']:
                        if doc.get(campo):
                            doc[campo] = str(doc[campo]).strip()

                    documentos.append(doc)

                if documentos:
                    collection.insert_many(documentos)
                    count += len(documentos)
                    print(f"✅ {count} registros inseridos no cluster MongoDB Atlas...")

        print(f"\n🚀 Migração concluída com sucesso! Banco: citsm_analyzer | Coleção: ods_itsm")

    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        if 'ora_conn' in locals(): ora_conn.close()
        if 'mongo_client' in locals(): mongo_client.close()

if __name__ == "__main__":
    migrar_para_citsm()