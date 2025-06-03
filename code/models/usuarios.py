import re

from services.bot_functions import BotClass
from services.database_functions import DataBase
from services.waha import WahaBot

db = DataBase()
waha = WahaBot()
bot = BotClass()

class Usuarios:

    def verificar_usuario(self, numero_telefone):
        try:
            consultar_usuario = "SELECT * FROM usuarios WHERE telefone = %s"
            params = (numero_telefone,)

            if db.execute_query(consultar_usuario, params):
                return True
            else:
                return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O USUÁRIO JÁ EXISTE')
            print(e)

    def cadastrar_usuario(self, formulario, chatId, numero_telefone):
        try:
            padrao = r"\*Digite seu nome!\s*:\*\s*(.*?)\s*(?:\n|\r|\r\n)?\s*\*Digite seu sobrenome!\s*:\*\s*(.*?)\s*(?:\n|\r|\r\n)?\s*\*Qual seu limite de gastos mensal\?\s*:\*\s*([\d.,]+)"

            match = re.search(padrao, formulario)

            nome = match.group(1).strip()
            sobrenome = match.group(2).strip()
            telefone = numero_telefone
            limite = int(match.group(3))
            
            columns = ('nome', 'sobrenome', 'telefone', 'limite')
            placeholders = ', '.join(['%s'] * len(columns))
            values = (nome, sobrenome, telefone, limite)
        
            create_usuario = (f"""INSERT INTO usuarios ({', '.join(columns)}) VALUES ({placeholders})""")
    
            db.execute_script(create_usuario, values)

            waha.send_message(chatId, 'Seu cadastro foi concluido com sucesso! Agora você pode enviar seus gastos e despesas aqui, assim, irei armazenar todas as informaçoes para você e você terá o controle dos seus gastos de forma muito mais fácil :)')

        except Exception as e:
            print(f'Erro ao adicionar informações do usuário')
            print(e)
            waha.send_message(chatId, 'Ocorreu um erro ao cadastrar seu usuário, a equipe técnica irá analisar o ocorrido!')
            bot.define_status(chatId, 'start')
            return