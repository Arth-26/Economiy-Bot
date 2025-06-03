import re

from models.extratos import Extratos
from utils import filtrar_digitos

from .waha import WahaBot

waha = WahaBot()
extrato = Extratos()

class BotClass:

    def __init__(self):
        self.__conversation_state = {}
        self.__etapas_cadastro = {}

    @property
    def get_conversation_state(self):
        return self.__conversation_state
       
        
    def define_status(self, chatId, status=None):
        if status:
            self.__conversation_state[chatId] = status
            state = self.__conversation_state[chatId]
        elif chatId in self.__conversation_state:
            state = self.__conversation_state[chatId]
        else:
            state = 'start'

        return state


    def define_proxima_mensagem(self, state, chatId, message_content):
        if state == 'start':
            message = '''Olá, bem vindo ao Economy Bot!\nVocê ainda não possui uma conta!\n\nDeseja cadastrar-se no nosso sistema de controle financeiro?\n\n\t 1- Sim\n\t 2- Não'''
            self.define_status(chatId, 'first_answer')
        elif state == 'first_answer':
            respostas_sim = {"1", "sim", "Sim", "SIM", "s", "S"}
            respostas_nao = {"2", "nao", "Nao", "NAO", "não", "Não", "NÃO", "n", "N"}
            if message_content.strip() in respostas_sim:
                message = '''Ótimo! Iremos prosseguir com seu cadastro! Por favor, preencha este formulário:\n https://whatsform.com/uucley'''
                self.define_status(chatId, 'cadastro')
            elif message_content.strip() in respostas_nao:
                message = 'Certo! Encerraremos nosso atendimento por aqui! Caso mude de ideia, é só chamar'
                self.define_status(chatId, 'start')
            else:
                message = 'Resposta inválida! Por favor, escolha Sim ou Não.'
        else:
            return
        
        waha.send_message(chatId, message)
        

    def captura_dados_mensagem(self, chatId, mensagem):
        dados = self.parse_entrada_data(mensagem)
        numero_telefone = filtrar_digitos(chatId)

        if type(dados) == str:
            waha.send_message(chatId, dados)
            raise Exception("Erro ao capturar dados da mensagem do usuário")

        try:
            _, mes, ano = dados['data'].split("/")

            if extrato.verifica_extrato_existe(numero_telefone, mes, ano):
                if extrato.cadastra_entrada(dados, mes, ano, chatId):
                    waha.send_message(chatId, mensagem)
            else:
                extrato.cria_extrato_usuario(numero_telefone, mes, ano)
                if extrato.cadastra_entrada(dados, mes, ano, chatId):
                    waha.send_message(chatId, mensagem)


        except Exception as e:
            print('Erro')
            print(e)

 
    def parse_entrada_data(self, entrada):
        try:
            padrao = re.compile(
                r"💲 Produto: (.+)\n"
                r"🔖 Descrição: (.+)\n"
                r"💰 Valor: R\$ ([\d,.]+)\n"
                r"🔄 Tipo: (?:🟩|🟥) (Receita|Despesa)\n" 
                r"📂 Categoria: (.+)\n"
                r"💳 Pagamento: (.+)\n"
                r"🗓️ Data: (\d{2}/\d{2}/\d{4})"
            )

            match = padrao.search(entrada)
            if not match:
                raise Exception("Formato da mensagem inválido. Verifique os campos e tente novamente.")

            if not match.group(3) or not match.group(4):
                raise ValueError("Ocorreu um erro ao cadastrar seu registro!\nCertifique-se de informar o valor e o tipo de registro (RECEITA OU DESPESA) antes de nos enviar.")
        
            dados = {
                "produto" : match.group(1).upper(),
                "descricao": match.group(2).upper(),
                "valor": match.group(3).replace('.', '').replace(',', '.'),
                "tipo": match.group(4).upper(),
                "categoria": match.group(5).upper(),
                "pagamento": match.group(6).upper(),
                "data": match.group(7),
            }

            self.valida_dados(dados)
            return dados

        except ValueError as ve:
            print("Erro de validação:", ve)
            return str(ve)

        except Exception as e:
            print('Falha ao capturar informações da entrada do usuário')
            print(e)
        
    def valida_dados(self, dados):
        if len(dados.get('produto')) > 100:
            raise Exception("O campo 'produto' excede o limite de 100 caracteres.")
        elif len(dados.get('categoria')) > 150:
            raise Exception("O campo 'categoria' excede o limite de 150 caracteres.")
        elif len(str(dados.get('valor'))) > 12:
            raise ValueError("Este valor é muito alto para cadastrar no nosso sistema!\n Nosso sistema é feito apenas para controle financeiro. Para transações desse nivel, aconselhamos procurar um profissional capacitado!")

        return True 