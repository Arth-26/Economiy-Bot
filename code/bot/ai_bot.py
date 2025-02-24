import os
from datetime import date

from decouple import config
from groq import Groq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from services.waha_bot import WahaBot

os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')

class LlamaClass:

    def __init__(self):
        self.waha = WahaBot()
        self.__client = ChatGroq(model='llama-3.3-70b-versatile')

    
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

            prompt = PromptTemplate(
                input_variables=['system_prompt', 'texto'],
                template='''
                    <system_prompt>
                        {system_prompt}
                    </system_prompt>
                    <texto>
                        {texto}
                    </texto>
                '''
            )
            chain = prompt | self.__client | StrOutputParser()
            response = chain.invoke({
                'system_prompt': system_instruction,
                'texto': text,
            })

            print(response)
            
            funcao = response
            match funcao:
                case 'NOT_FUNCTION':
                    self.mensagem_exemplo(chatId)
                case 'FIN_FUNCTION':
                    self.cadastrar_entrada(chatId, text)
                case 418:
                    return "I'm a teapot"


        except Exception as e:
            print('Deu ruim')
            print(e)

    def mensagem_exemplo(self, chatId):
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

    def cadastrar_entrada(self, chatId, text):
        client = self.__client
        waha = self.waha
        hoje = date.today()
        try:
            system_instruction = f'''Você é um assistente financeiro que registra transações com base na mensagem do usuário. Identifique se é um gasto (🟥 Despesa) ou um ganho (🟩 Receita) e extraia os dados seguindo este formato:

            📋 Resumo da Transação
            ───────────────────
            🔖 Descrição: [Motivo ou item] (se ausente, "Não definido")
            💰 Valor: R$ [Montante] (obrigatório, solicite se ausente)
            🔄 Tipo: [🟥 Despesa | 🟩 Receita] (obrigatório, solicite se ausente)
            📂 Categoria: [Tipo de gasto/ganho] (se não conseguir identificar a categoria, "Não definido")
            🏦 Conta: [Origem/destino] (se ausente, "Conta pessoal")
            💳 Pagamento: [Pix, débito, crédito, etc.] (se ausente, "Dinheiro")
            🗓️ Data: [DD/MM/AAAA] (se "ontem" ou "há X dias", converter; se ausente, usar {hoje})

            Se valor ou tipo não forem identificados, não cadastre e peça que o usuário use termos como "gastei", "paguei", "recebi", "ganhei", fornecendo exemplos.

            Se a transação for registrada, confirme com uma mensagem amigável e um toque de humor sobre o gasto.

            Se não for possível identificar se foi um gasto ou um ganho, responda exatamente: "Desculpe, não consegui identificar se foi um gasto ou um ganho. Por favor! Seja explicito na sua mensagem para que eu possa processar as informações corretamente"'''

            prompt = PromptTemplate(
                input_variables=['system_prompt', 'texto'],
                template='''
                    <system_prompt>
                        {system_prompt}
                    </system_prompt>
                    <texto>
                        {texto}
                    </texto>
                '''
            )
            chain = prompt | self.__client | StrOutputParser()
            response = chain.invoke({
                'system_prompt': system_instruction,
                'texto': text,
            })
            
            waha.send_message(chatId, response)

        except Exception as e:
            print('Deu ruim')
            print(e)





