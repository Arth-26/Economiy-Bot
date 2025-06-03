import os
import json

from decouple import config
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_groq import ChatGroq

os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')

client = ChatGroq(model='llama-3.3-70b-versatile')

arquivo_json = 'project_files/scripts/scripts.json'

with open(arquivo_json, 'r', encoding='utf-8') as f:
    consultas = json.load(f)

documentos = []

for consulta, infos in consultas.items():
    query = infos.get('query')
    exemplos = infos.get('examples')

    for tipo, perguntas in exemplos.items():
        for pergunta in perguntas:
            doc = Document(
                    page_content=pergunta,
                    metadata = {
                        "consulta": consulta,
                        "tipo": tipo,
                        "query": query
                    }      
                )  
            documentos.append(doc) 

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

banco_vetores = FAISS.from_documents(documentos, embedding_model)

def buscar_sql(pergunta):
    resultados = banco_vetores.similarity_search(pergunta, k=1)

    if not resultados:
        return 'Nada encontrado'
    
    resultado = resultados[0]
    metadata = resultado.metadata

    return {
        "pergunta_usuario": pergunta,
        "pergunta_encontrada": resultado.page_content,
        "consulta": metadata.get("consulta"),
        "tipo": metadata["tipo"],
        "query": metadata["query"]
    }


resultado = buscar_sql('Quanto recebi na mês passado?')

if resultado:
    print("📌 Pergunta do usuário:", resultado["pergunta_usuario"])
    print("🔍 Pergunta encontrada:", resultado["pergunta_encontrada"])
    print("📄 Consulta identificada:", resultado["consulta"])
    print("📂 Tipo de entrada:", resultado["tipo"])
    print("🧾 SQL:", resultado["query"])
else:
    print("Nenhuma correspondência encontrada.")