from datetime import datetime

from services.database_functions import DataBase
from services.waha import WahaBot
from utils import filtrar_digitos

db = DataBase()
waha = WahaBot()
class Extratos:

    def verifica_extrato_existe(self, telefone_usuario, mes, ano):
        try:
            consulta_extrato = """SELECT e.* FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = %s AND e.mes = %s  AND e.ano = %s """
            params = (f'{telefone_usuario}', mes, ano)
            if db.execute_query(consulta_extrato, params):
                return True
            else:
                return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O EXTRATO JÁ EXISTE')
            print(e)


    def cria_extrato_usuario(self, telefone_usuario, mes, ano):
        try:
            columns = ('usuario_id', 'mes', 'ano')
            values = (f'{telefone_usuario}', mes, ano)
            cria_extrato = f"""INSERT INTO extratos ({', '.join(columns)})
            VALUES ((SELECT id FROM usuarios WHERE telefone = %s), %s, %s)"""

            db.execute_script(cria_extrato, values)
        except Exception as e:
            print('ERRO AO CRIAR EXTRATO')
            print(e)


    def cadastra_entrada(self, dados, mes, ano, chatId):
        try:
            numero_telefone = filtrar_digitos(chatId)
            extrato_id = """SELECT e.id FROM extratos e INNER JOIN usuarios u ON e.usuario_id = u.id WHERE telefone = %s AND e.mes = %s AND e.ano = %s LIMIT 1"""
            params = (f'{numero_telefone}', mes, ano)

            extrato = db.execute_query(extrato_id, params)

            dados['data'] = datetime.strptime(dados['data'], "%d/%m/%Y")

            dados['data'] = dados['data'].strftime("%Y-%m-%d")

            columns = ('extrato_id', 'produto', 'categoria', 'tipo', 'data', 'valor', 'tipo_pagamento', 'descricao')
            values = (extrato[0], dados['produto'], dados['categoria'], dados['tipo'], dados['data'], dados['valor'], dados['pagamento'], dados['descricao'])
            placeholders = ', '.join(['%s'] * len(columns))

            cadastro_entrada = f"""INSERT INTO entradas ({', '.join(columns)}) VALUES ({placeholders})"""

            if db.execute_script(cadastro_entrada, values) == True:
                return True
            else:
                raise
        except Exception as e:
            print('Erro ao cadastrar entrada')
            print(e)
            return False