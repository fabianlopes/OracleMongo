import os
import oracledb
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def extrair_metadados(cursor, nome_tabela):
    """Lê o dicionário de dados do Oracle para entender o cubo."""
    print(f"🧐 Analisando arquitetura da tabela: {nome_tabela}...")
    sql = f"""
        SELECT column_name, data_type, data_precision, data_scale 
        FROM user_tab_columns 
        WHERE table_name = '{nome_tabela.upper()}'
    """
    cursor.execute(sql)
    return cursor.fetchall()

def migrar_cubo(nome_tabela_oracle, colecao_mongo):
    # Conexões
    ora_conn = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASS"),
        dsn=os.getenv("ORACLE_DSN")
    )
    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    db = mongo_client['pericia_db']
    col = db[colecao_mongo]

    try:
        with ora_conn.cursor() as cursor:
            # 1. Entender a tabela
            metadados = extrair_metadados(cursor, nome_tabela_oracle)
            colunas = [m[0] for m in metadados]

            # 2. Buscar os dados do Cubo
            print(f"🚀 Iniciando extração de dados...")
            cursor.execute(f"SELECT * FROM {nome_tabela_oracle}")

            # 3. Processar em lotes para não sobrecarregar a rede da Secretaria
            while True:
                linhas = cursor.fetchmany(1000)
                if not linhas:
                    break

                documentos = []
                for linha in linhas:
                    # Cria o JSON mapeando cada coluna ao seu valor
                    doc = dict(zip(colunas, linha))
                    # Aqui você pode adicionar lógica de limpeza/perícia
                    documentos.append(doc)

                if documentos:
                    col.insert_many(documentos)
                    print(f"✅ Inseridos {len(documentos)} registros no MongoDB Atlas...")

    finally:
        ora_conn.close()
        mongo_client.close()

if __name__ == "__main__":
    # Substitua pelo nome real da tabela do seu cubo
    Tabela_Alvo = "NOME_DA_SUA_TABELA_AQUI"
    migrar_cubo(Tabela_Alvo, "cubo_bi_investigacao")