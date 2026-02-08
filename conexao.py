import os
from pymongo import MongoClient
from dotenv import load_dotenv
import oracledb
import os

load_dotenv()

def test_mongo():
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        # O comando 'ping' confirma se a autenticação e o IP estão OK
        client.admin.command('ping')
        print("✅ Conexão com o MongoDB Atlas realizada com sucesso!")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

if __name__ == "__main__":
    test_mongo()

def test_oracle():
    try:
        # Tenta conectar usando as variáveis do seu .env
        conn = oracledb.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASS"),
            dsn=os.getenv("ORACLE_DSN")
        )
        print(f"✅ Conexão com Oracle (Versão {conn.version}) OK!")
        conn.close()
    except Exception as e:
        print(f"❌ Erro no Oracle: {e}")

if __name__ == "__main__":
    test_oracle()