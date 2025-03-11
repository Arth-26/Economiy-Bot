from services.database_functions import DataBase
from services.waha import WahaBot
import re

db = DataBase()
waha = WahaBot()

class Usuarios:

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

    def cadastrar_usuario(self, formulario, chatId, numero_telefone):
        try:
            padrao = r"\*Digite seu nome!\s*:\*\s*(.+)\n.*?sobrenome!\s*:\*\s*(.+)\n.*?gastos mensal\?\s*:\*\s*(\d+)\n.*?identificação\s*:\*\s*(\S+)"

            match = re.search(padrao, formulario)

            nome = match.group(1).strip()
            sobrenome = match.group(2).strip()
            telefone = numero_telefone
            limite = int(match.group(3))
            chave_acesso = match.group(4).strip()
            
        
            create_usuario = f"""INSERT INTO usuarios (nome, sobrenome, telefone, limite, senha) VALUES ('{nome}', '{sobrenome}', '{telefone}', {limite}, '{chave_acesso}')"""
    
            db.execute_script(create_usuario)

            waha.send_message(chatId, 'Seu cadastro foi concluido com sucesso! Agora você pode enviar seus gastos e despesas aqui, assim, irei armazenar todas as informaçoes para você e você terá o controle dos seus gastos de forma muito mais fácil :)')

        except Exception as e:
            print(f'Erro ao adicionar informações do usuário')
            print(e)
            waha.send_message(chatId, 'Ocorreu um erro ao cadastrar seu usuário, a equipe técnica irá analisar o ocorrido!')
            self.define_status(chatId, 'start')