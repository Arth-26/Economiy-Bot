import json
import os
import tempfile
from collections import defaultdict
from datetime import date
from decimal import Decimal

import pandas as pd
from decouple import config
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from utils import filtrar_digitos, formatar_valor_brasileiro, ler_arquivo

from .bot_class import BotClass
from .database_class import DataBase
from .waha import WahaBot

os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')


class LlamaClass:

    def __init__(self):
        self.waha = WahaBot()
        self.db = DataBase()
        self.api = BotClass()
        self.__client = ChatGroq(model='llama-3.3-70b-versatile')

    def identificar_funcao(self, text):
        """
        Usa uma LLM para identificar se a mensagem é de consulta, cadastro ou irrelevante.
        """
        client = self.__client

        try:
            system_instruction = ler_arquivo('code/prompts/identificar_funcao.txt', 'text')
            chain = (
                PromptTemplate.from_template(
                    '''
                        {system_prompt}

                        A mensagem do usuário é:
                        
                        {texto}
                    '''
                ) 
                | client 
                | StrOutputParser()
            )
            
            response = chain.invoke({
                'system_prompt': system_instruction,
                'texto': text,
            })
            
            return response
        except Exception as e:
            print('Deu ruim')
            print(e)

    def executa_funcao(self, chatId, text):
        """
            Executa uma função com base na intenção identificada:
            - NOT_FUNCTION: resposta neutra
            - FIN_FUNCTION: cadastro de entrada
            - QUERY_FUNCTION: consulta de dados
        """
        funcao = self.identificar_funcao(text)
        match funcao:
            case 'NOT_FUNCTION':
                self.funcao_nao_identificada(chatId)
            case 'FIN_FUNCTION':
                self.gerar_mensagem_cadastro(chatId, text)
            case 'QUERY_FUNCTION':
                self.mostra_resultados_consulta_usuario(chatId, text)

    def funcao_nao_identificada(self, chatId):
        """
        Envia uma mensagem ao usuário se não entender a intenção.
        """

        waha = self.waha
        mensagem = '''Hmm... Não consegui entender se você quer consultar seu extrato ou registrar uma nova transação. 🤔

        Se quiser consultar seus gastos ou receitas passadas, tente algo como:
        ➡️ "Quanto gastei este mês?"
        ➡️ "Me mostre meu extrato da semana passada."

        Se quiser registrar um novo gasto ou receita, tente algo como:
        ✅ "Gastei 50 reais no mercado."
        ✅ "Recebi 200 reais do meu cliente."

        Me envie a mensagem novamente de forma mais clara, e eu te ajudo! 🚀'''
        
        waha.send_message(chatId, mensagem)

    def gerar_mensagem_cadastro(self, chatId, text):
        """
            Usa a LLM para transformar uma frase natural do usuário em uma mensagem estruturada,
            e envia para a lógica de cadastro (`captura_dados_mensagem`)
        """

        client = self.__client
        api = self.api
        hoje = date.today()
        try:
            system_instruction = ler_arquivo("code/prompts/gerar_mensagem_cadastro.txt", 'text').replace('{{data_hoje}}', f'{hoje}')

            chain = (
                PromptTemplate.from_template(
                    '''
                        {system_prompt}

                        A mensagem do usuário é:
                        
                        {texto}
                    '''
                ) 
                | client 
                | StrOutputParser()
            )
            response = chain.invoke({
                'system_prompt': system_instruction,
                'texto': text,
            })
            
            # Captura os dados do texto estruturado
            api.captura_dados_mensagem(chatId, response)
            
        except Exception as e:
            print('ERRO NO PROCESSO DE GERAÇÃO DE MENSAGEM DE CADASTRO DA ENTRADA DO USUÁRIO')
            print(e)

    def selecionar_query_por_similaridade(self, text):
        """
        Utiliza embeddings para encontrar a consulta SQL mais próxima da intenção do usuário.
        """

        consultas = ler_arquivo("../project_files/scripts/banco_vetores.json", 'json')
        
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

        # Carrega modelo de embeddings
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Cria o índice vetorial
        banco_vetores = FAISS.from_documents(documentos, embedding_model)

        # Busca a consulta mais próxima
        resultados = banco_vetores.similarity_search(text, k=1)

        if not resultados:
            return 'Nada encontrado'
        
        resultado = resultados[0]
        metadata = resultado.metadata

        return {
            "tipo": metadata["tipo"],
            "query": metadata["query"]
        }
    
    def processar_consulta_do_usuario(self, chatId, text):
        """
        Processa uma consulta identificada via similaridade, executa a query no banco
        e retorna os resultados brutos.
        """
        
        resultado_consulta = self.selecionar_query_por_similaridade(text)

        numero_telefone = filtrar_digitos(chatId)
        tipo = resultado_consulta.get('tipo')

        query = resultado_consulta.get('query')
        params = (f'{numero_telefone}', tipo)
        
        resultados = self.db.execute_query(query, params)

        return resultados
    
    def mostra_resultados_consulta_usuario(self, chatId, text):
        """
            Formata e envia para o usuário os resultados de uma consulta.
            Agrupa por categoria, soma os valores e detalha os itens.
        """
        resultados = self.processar_consulta_do_usuario(chatId, text)
        if len(resultados) < 1:
            message = '''Você não possui nenhum registro no período informado!
            
            Você pode cadastrar novos registros nos enviando uma mensagem do tipo
            "GASTEI 20 REAIS COM ALIMENTAÇÃO",
            "RECEBI 50 REAIS COM SERVIÇOS EXTRAS"
            
            Nós iremos armazenar essas informações e te retornar sempre que você precisar 😊'''
        else:
            resultados_por_categoria = defaultdict(lambda: {"itens": [], "total": Decimal('0.00')})

            for item in resultados:
                categoria = item[1]
                valor = item[3]
                resultados_por_categoria[categoria]["itens"].append(item)
                resultados_por_categoria[categoria]["total"] += valor

            valor_total_consulta = sum(info["total"] for info in resultados_por_categoria.values())
            message = f'''Você possui {len(resultados)} registros no período consultado com um valor total de R$ {formatar_valor_brasileiro(valor_total_consulta)}'''

            for categoria, info in resultados_por_categoria.items():
                message += f'\n\n💲{categoria.upper()}: R$ {formatar_valor_brasileiro(info["total"])}'
                for item in info["itens"]:
                    produto = item[0]
                    data = item[2].strftime('%d/%m/%Y')
                    valor = item[3]
                    forma_pagamento = item[4]
                    message += f'\n- {data}: {produto} - R$ {formatar_valor_brasileiro(valor)} ({forma_pagamento})'

        # Envia a consulta completamente formatada para o usuário
        self.waha.send_message(chatId, message)