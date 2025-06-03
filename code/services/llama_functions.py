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
from utils import filtrar_digitos, formatar_valor_brasileiro

from .bot_functions import BotClass
from .database_functions import DataBase
from .waha import WahaBot

os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')


class LlamaClass:

    def __init__(self):
        self.waha = WahaBot()
        self.db = DataBase()
        self.api = BotClass()
        self.__client = ChatGroq(model='llama-3.3-70b-versatile')

    def load_scripts(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print('Arquivo não encontrado')
            return {}

    def identificar_função(self, chatId, text):
        client = self.__client

        try:
            system_instruction = f'''Você é um assistente financeiro responsável por identificar a ação desejada com base na mensagem do usuário. Classifique a mensagem em um dos seguintes três casos de uso e retorne **exatamente** a string correspondente:

                                    1 **Caso: QUERY_FUNCTION**  
                                    Se a mensagem indica que o usuário quer **consultar** informações sobre suas finanças passadas, como:  
                                    - Extrato  
                                    - Total gasto em um período  
                                    - Total recebido  
                                    - Histórico de transações  
                                    - Comparação de receitas e despesas  

                                    **Exemplos de mensagens que devem retornar QUERY_FUNCTION:**  
                                    - "Quanto gastei semana passada?"  
                                    - "Quero ver meu extrato"  
                                    - "Quanto recebi este mês?"  
                                    - "Me mostre todas as despesas dos últimos 30 dias"  
                                    - "Qual foi minha maior despesa do mês?"  

                                    2 **Caso: FIN_FUNCTION**  
                                    Se a mensagem indica que o usuário quer **registrar** uma nova transação, e contém palavras-chave como **"gastei", "paguei", "recebi", "ganhei"**, ou outras que sinalizam um giro de capital no contexto de um novo registro.  

                                    **Exemplos de mensagens que devem retornar FIN_FUNCTION:**  
                                    - "Gastei 50 reais no mercado"  
                                    - "Recebi 200 reais do meu cliente"  
                                    - "Paguei o aluguel ontem"  
                                    - "Ganhei um bônus de 500 reais"  
                                    - "Registre que comprei um celular novo"  

                                    3 **Caso: NOT_FUNCTION**  
                                    Se a mensagem **não se encaixa** claramente nos dois casos anteriores ou é ambígua, **retorne NOT_FUNCTION**.  

                                    **Exemplos de mensagens que devem retornar NOT_FUNCTION:**  
                                    - "Estou preocupado com minhas finanças"  
                                    - "Preciso economizar mais"  
                                    - "O que devo fazer para gastar menos?"  
                                    - "Qual investimento você recomenda?"  

                                    **Regras Importantes para Evitar Conflitos:**  
                                    - Se a mensagem perguntar sobre valores passados (**"Quanto gastei?"**, **"Quanto recebi?"**), classifique como `QUERY_FUNCTION`.  
                                    - Se a mensagem indicar uma ação concreta de **registrar** um novo gasto ou receita, classifique como `FIN_FUNCTION`.  
                                    - Se não for possível determinar com clareza, classifique como `NOT_FUNCTION`.  

                                    **Retorne APENAS a string correspondente (QUERY_FUNCTION, FIN_FUNCTION ou NOT_FUNCTION), sem nenhuma explicação adicional.**'''

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
            
            funcao = response
            match funcao:
                case 'NOT_FUNCTION':
                    self.funcao_nao_identificada(chatId)
                case 'FIN_FUNCTION':
                    self.gerar_mensagem_cadastro(chatId, text)
                case 'QUERY_FUNCTION':
                    self.mostra_resultados_consulta_usuario(chatId, text)


        except Exception as e:
            print('Deu ruim')
            print(e)

    def funcao_nao_identificada(self, chatId):
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
        client = self.__client
        api = self.api
        hoje = date.today()
        try:
            system_instruction = f'''Você é um assistente financeiro que registra transações com base na mensagem do usuário. Identifique se é um gasto (🟥 Despesa) ou um ganho (🟩 Receita) e extraia os dados seguindo este formato:

            📋 Resumo da Transação
            ───────────────────
            💲 Produto: [Item] (se ausente, "Não definido")
            🔖 Descrição: [Motivo] (se ausente, "Não definido")
            💰 Valor: R$ [Montante] (obrigatório, solicite se ausente) (SISTEMA MONETÁRIO BRASILEIRO)
            🔄 Tipo: [🟥 Despesa | 🟩 Receita] (obrigatório, solicite se ausente)
            📂 Categoria: [ALIMENTAÇÃO, LAZER, IMÓVEL, ELETRÔNICOS, VEICULOS, GASTOS BÁSICOS, OUTROS] (se não conseguir identificar a categoria, "Não definido")
            💳 Pagamento: [Pix, débito, crédito, etc.] (se ausente, "Dinheiro")
            🗓️ Data: [DD/MM/AAAA] (se "ontem" ou "há X dias", converter; se ausente, usar {hoje})

            Se valor ou tipo não forem identificados, não cadastre e peça que o usuário use termos como "gastei", "paguei", "recebi", "ganhei", fornecendo exemplos.

            Se a transação for registrada, confirme com uma mensagem amigável e um toque de humor sobre o gasto.

            Se não for possível identificar se foi um gasto ou um ganho, responda exatamente: "Desculpe, não consegui identificar se foi um gasto ou um ganho. Por favor! Seja explicito na sua mensagem para que eu possa processar as informações corretamente
            
            EXEMPLOS DE RESPOSTAS:

            Usuário: "Paguei R$ 129,90 no cartão para recarregar meu celular"
            Resposta:
            ✅ Tim-tim pro seu saldo! 
            📋 Resumo da Transação
            ───────────────────
            💲 Produto: Recarga celular
            🔖 Descrição: Não definido
            💰 Valor: R$ 129.90
            🔄 Tipo: 🟥 Despesa
            📂 Categoria: Outros
            💳 Pagamento: Crédito
            🗓️ Data: 15/07/2024

            "Recarga vitalícia? Espero que tenha crédito até pro ano que vem! 😉"'''

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
            
            api.captura_dados_mensagem(chatId, response)
            
        except Exception as e:
            print('ERRO NO PROCESSO DE GERAÇÃO DE MENSAGEM DE CADASTRO DA ENTRADA DO USUÁRIO')
            print(e)

    def selecionar_query_por_similaridade(self, text):
        arquivo = "../project_files/scripts/scripts.json"
        with open(arquivo, 'r', encoding='utf-8') as f:
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
        resultado_consulta = self.selecionar_query_por_similaridade(text)

        numero_telefone = filtrar_digitos(chatId)
        tipo = resultado_consulta.get('tipo')

        query = resultado_consulta.get('query')
        params = (f'{numero_telefone}', tipo)
        
        resultados = self.db.execute_query(query, params)

        return resultados
    
    def mostra_resultados_consulta_usuario(self, chatId, text):
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