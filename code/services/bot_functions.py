import re
from datetime import datetime

from utils import filtrar_digits

from .database_functions import DataBase
from .waha import WahaBot

db = DataBase()
waha = WahaBot()

class BotClass:

    def __init__(self):
        self.__conversation_state = {}
        self.__etapas_cadastro = {}

    @property
    def get_conversation_state(self):
        return self.__conversation_state
    

    # CLASSE USUARIO
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
        
    # CLASSE USUÁRIO
    def inserir_proximo_campo(self, formulario, chatId, numero_telefone):
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

    # CLASSE EXTRATO
    def verifica_extrato_existe(self, telefone_usuario, mes, ano):
        try:
            consulta_extrato = f"""SELECT e.* FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = '{telefone_usuario}' AND e.mes = {mes} AND e.ano = {ano}"""

            if db.execute_query(consulta_extrato):
                return True
            else:
                return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O EXTRATO JÁ EXISTE')
            print(e)


    def captura_dados_mensagem(self, chatId, mensagem):
        dados = self.parse_entrada_data(mensagem)
        numero_telefone = filtrar_digits(chatId)

        try:
            _, mes, ano = dados['data'].split("/")

            if self.verifica_extrato_existe(numero_telefone, mes, ano):
                if self.cadastra_entrada(dados, numero_telefone, mes, ano):
                    waha.send_message(chatId, mensagem)
            else:
                self.cria_extrato_usuario(numero_telefone, mes, ano)
                if self.cadastra_entrada(dados, numero_telefone, mes, ano):
                    waha.send_message(chatId, mensagem)


        except Exception as e:
            print('Erro')
            print(e)

    # CLASSE EXTRATO
    def cria_extrato_usuario(self, telefone_usuario, mes, ano):
        try:
            cria_extrato = f"""INSERT INTO extratos (usuario_id, mes, ano)
            VALUES (
                (SELECT id FROM usuarios WHERE telefone = '{telefone_usuario}'),
                {mes},
                {ano}
            )"""

            db.execute_script(cria_extrato)
        except Exception as e:
            print('ERRO AO CRIAR EXTRATO')
            print(e)

    # CLASSE EXTRATO
    def cadastra_entrada(self, dados, telefone_usuario, mes, ano):
        try:
            extrato_id = f"""SELECT e.id FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = '{telefone_usuario}' AND e.mes = {mes} AND e.ano = {ano}"""

            dados['data'] = datetime.strptime(dados['data'], "%d/%m/%Y")

            dados['data'] = dados['data'].strftime("%Y-%m-%d")

            cadastro_entrada = f"""INSERT INTO compras (extrato_id, produto, categoria, tipo, data, valor, tipo_pagamento, descricao)
            VALUES (({extrato_id}), '{dados['produto']}', '{dados['categoria']}', '{dados['tipo']}', '{dados['data']}', {dados['valor']}, '{dados['pagamento']}', '{dados['descricao']}')"""

            db.execute_script(cadastro_entrada)

            return True
        except Exception as e:
            print('Erro ao cadastrar entrada')
            print(e)

            return False
        
    
    def parse_entrada_data(entrada):
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
        
            dados = {
                "produto" : match.group(1).upper(),
                "descricao": match.group(2).upper(),
                "valor": match.group(3).replace(',', '.'),
                "tipo": match.group(4).upper(),
                "categoria": match.group(5).upper(),
                "pagamento": match.group(6).upper(),
                "data": match.group(7),
            }

            return dados

        except Exception as e:
            print('Falha ao capturar informações da entrada do usuário')