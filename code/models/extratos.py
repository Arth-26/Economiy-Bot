from datetime import datetime

from services.database_class import DataBase
from services.waha import WahaBot
from utils import filtrar_digitos

db = DataBase()
waha = WahaBot()
class Extratos:

    def verifica_extrato_existe(self, telefone_usuario, mes, ano):
        """
            Verifica se já existe um extrato cadastrado no banco de dados para o usuário informado
            com base no número de telefone, mês e ano especificados.

            Retorna:
                True se o extrato existir, False caso contrário.
        """
         
        try:
            # Consulta SQL para verificar se já existe um extrato para o telefone, mês e ano informados
            consulta_extrato = """SELECT e.* FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = %s AND e.mes = %s  AND e.ano = %s """
            params = (f'{telefone_usuario}', mes, ano)

            # Executa a consulta e verifica se algum resultado foi retornado
            if db.execute_query(consulta_extrato, params):
                return True
            return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O EXTRATO JÁ EXISTE')
            print(e)


    def cria_extrato_usuario(self, telefone_usuario, mes, ano):
        """
            Cria um novo extrato para o usuário com base no telefone, mês e ano fornecidos.
            O ID do usuário é obtido dinamicamente a partir do número de telefone.
        """
        try:
            # Define as colunas e valores a serem inseridos no extrato
            columns = ('usuario_id', 'mes', 'ano')
            values = (f'{telefone_usuario}', mes, ano)

            # Comando SQL de inserção usando subconsulta para pegar o ID do usuário
            cria_extrato = f"""INSERT INTO extratos ({', '.join(columns)})
            VALUES ((SELECT id FROM usuarios WHERE telefone = %s), %s, %s)"""

            # Executa o comando de inserção
            db.execute_script(cria_extrato, values)
        except Exception as e:
            print('ERRO AO CRIAR EXTRATO')
            print(e)


    def cadastra_entrada(self, dados, mes, ano, chatId):
        """
            Registra uma nova entrada (transação) no extrato do usuário correspondente ao mês e ano.

            Parâmetros:
                dados: dicionário contendo informações da transação
                mes: mês da transação
                ano: ano da transação
                chatId: identificador do usuário no chat (usado para extrair o telefone)

            Retorna:
                True se o registro for bem-sucedido, False em caso de erro.
        """
        try:
            # Extrai e filtra apenas os dígitos do telefone a partir do chatId
            numero_telefone = filtrar_digitos(chatId)

            # Consulta o ID do extrato do usuário correspondente ao mês/ano
            extrato_id = """SELECT e.id FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = %s AND e.mes = %s AND e.ano = %s LIMIT 1"""
            params = (f'{numero_telefone}', mes, ano)

            # Executa a query para consultar o extrato
            extrato = db.execute_query(extrato_id, params)

            # Converte a data no formato dd/mm/yyyy para o formato yyyy-mm-dd (usado pelo banco)
            dados['data'] = datetime.strptime(dados['data'], "%d/%m/%Y")
            dados['data'] = dados['data'].strftime("%Y-%m-%d")

            # Define as colunas e valores para o cadastro da entrada
            columns = ('extrato_id', 'produto', 'categoria', 'tipo', 'data', 'valor', 'tipo_pagamento', 'descricao')
            values = (extrato[0], dados['produto'], dados['categoria'], dados['tipo'], dados['data'], dados['valor'], dados['pagamento'], dados['descricao'])
            
            # Monta os placeholders para a query de inserção
            placeholders = ', '.join(['%s'] * len(columns))

            # Monta e executa a query de inserção na tabela entradas
            cadastro_entrada = f"""INSERT INTO entradas ({', '.join(columns)}) VALUES ({placeholders})"""

            if db.execute_script(cadastro_entrada, values) == True:
                return True
            else:
                raise
        except Exception as e:
            print('Erro ao cadastrar entrada')
            print(e)
            return False