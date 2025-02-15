from .database_functions import DataBase
from .waha_bot import WahaBot

db = DataBase()
waha = WahaBot()

class ApiClass:

    def __init__(self):
        self.__conversation_state = {}
        self.__etapas_cadastro = {}

    @property
    def get_conversation_state(self):
        return self.__conversation_state

    def verificar_usuario(self, numero_telefone):

        consultar_usuario = f'SELECT * FROM usuarios WHERE telefone = {numero_telefone}'

        if db.execute_query(consultar_usuario):
            return True
        else:
            return False
        
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
            message = 'Olá, bem vindo ao Economy Bot!\nVocê ainda não possui uma conta!\n\nDeseja cadastrar-se no nosso sistema de controle financeiro?\n\n\t 1- Sim\n\t 2- Não'
            waha.send_message(chatId, message)
            self.define_status(chatId, 'first_answer')
        elif state == 'first_answer':
            if message_content == '1':
                message = 'Ótimo! Iremos prosseguir com seu cadastro!'
                waha.send_message(chatId, message)
                self.define_status(chatId, 'cadastro')
            elif message_content == '2':
                message = 'Certo! Encerraremos nosso atendimento por aqui! Caso mude de ideia, é só chamar'
                waha.send_message(chatId, message)
                self.define_status(chatId, 'start')
            else:
                message = 'Resposta inválida! Por favor, escolha 1 ou 2.'
                waha.send_message(chatId, message)
                return
        else:
            return
    

