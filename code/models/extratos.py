from services.database_functions import DataBase
from datetime import datetime

db = DataBase()

class Extratos:

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