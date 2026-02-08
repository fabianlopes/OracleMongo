from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client['citsm_analyzer']
collection = db['ods_itsm']

# Criando o índice de texto nos campos que o Orquestrador vai pesquisar
print("🔍 Criando índice de texto para o PMO Virtual...")
collection.create_index([
    ("RESUMO_TICKET", "text"),
    ("DESCRICAO", "text"),
    ("SISTEMA", "text")
], name="pmo_text_index")

print("✅ Índice criado com sucesso!")