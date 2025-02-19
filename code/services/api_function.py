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
        try:
            consultar_usuario = f"SELECT * FROM usuarios WHERE telefone = '{numero_telefone}'"

            if db.execute_query(consultar_usuario):
                return True
            else:
                return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O USUÁRIO JÁ EXISTE')
            print(e)
        
    def adicionar_usuario(self, telefone):
        try:
            adicionar_usuario_script = f"INSERT INTO usuarios (telefone) VALUES ('{telefone}')"

            db.execute_script(adicionar_usuario_script)
        except Exception as e:
            print('ERRO AO CRIAR USUÁRIO')
            print(e)
        
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
            message = '''Olá, bem vindo ao Economy Bot!\n Você ainda não possui uma conta!\n\n Deseja cadastrar-se no nosso sistema de controle financeiro?\n\n\t 1- Sim\n\t 2- Não'''
            self.define_status(chatId, 'first_answer')
        elif state == 'first_answer':
            if message_content == '1':
                message = 'Ótimo! Iremos prosseguir com seu cadastro! Por favor, digite seu nome.'
                self.define_status(chatId, 'cadastro')
            elif message_content == '2':
                message = 'Certo! Encerraremos nosso atendimento por aqui! Caso mude de ideia, é só chamar'
                self.define_status(chatId, 'start')
            else:
                message = 'Resposta inválida! Por favor, escolha 1 ou 2.'
                return
        else:
            return
        
        waha.send_message(chatId, message)
        

    def prosseguir_cadastro(self, numero_telefone):
        query = f"""
            SELECT nome, sobrenome, limite, senha
            FROM usuarios
            WHERE telefone = '{numero_telefone}'
        """
        resultado = db.execute_query(query)

        if not resultado:
            return None 

        
        dados = resultado[0]

        campos = ["nome", "sobrenome", "limite", "senha"]

        for i, campo in enumerate(campos):
            if dados[i] is None:  
                return campo 

        return "completo" 
    
    
    def verificar_proximo_campo(self, chatId, numero_telefone):
        proximo_campo = self.prosseguir_cadastro(numero_telefone)

        if proximo_campo == "nome":
            mensagem = "Qual é o seu nome?"
        elif proximo_campo == "sobrenome":
            mensagem = "Agora digite seu sobrenome!"
        elif proximo_campo == "limite":
            mensagem = "Qual o limite de gastos que você pode alcançar?"
        elif proximo_campo == "senha":
            mensagem = "Crie uma senha para sua conta.\n"
            mensagem += '''Essa senha serve para que caso outra pessoa tenha acesso ao seu número de alguma forma, ele não tenha acesso aos seus extratos.'''
        elif proximo_campo == "completo":
            self.define_status(chatId, 'concluido')

        waha.send_message(chatId, mensagem)


    def inserir_proximo_campo(self, campo, valor_campo, chatId, numero_telefone):
        campos = ['nome', 'sobrenome', 'limite', 'senha']
        campos.index(campo)
        
        try:
            update_field = f"""UPDATE usuarios SET {campo} = '{valor_campo}' WHERE telefone = '{numero_telefone}'"""

            db.execute_script(update_field)
            self.verificar_proximo_campo(chatId, numero_telefone)

        except Exception as e:
            print(f'Erro ao adicionar {campo} ao usuário')
            print(e)

