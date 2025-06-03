import re

from services.bot_class import BotClass
from services.database_class import DataBase
from services.waha import WahaBot

db = DataBase()
waha = WahaBot()
bot = BotClass()

class Usuarios:

    def verificar_usuario(self, numero_telefone):
        """
            Verifica se o número de telefone informado já está cadastrado como usuário no banco de dados.

            Parâmetros:
                numero_telefone: str - telefone a ser verificado.

            Retorna:
                True se o usuário já existir, False caso contrário.
        """
        try:
            # Consulta SQL para verificar existência de um usuário com o telefone fornecido
            consultar_usuario = "SELECT * FROM usuarios WHERE telefone = %s"
            params = (numero_telefone,)

            # Retorna True se houver resultados, senão False
            if db.execute_query(consultar_usuario, params):
                return True
            else:
                return False
        except Exception as e:
            print('ERRO AO VERIFICAR SE O USUÁRIO JÁ EXISTE')
            print(e)

    def cadastrar_usuario(self, formulario, chatId, numero_telefone):
        """
        Cadastra um novo usuário com base nas informações extraídas de um formulário preenchido no chat.

        Parâmetros:
            formulario: str - mensagem enviada pelo usuário contendo nome, sobrenome e limite.
            chatId: str - identificador do usuário no chat.
            numero_telefone: str - telefone do usuário.

        Ação:
            Insere o usuário na tabela `usuarios` e envia confirmação via WhatsApp.
            Em caso de erro, envia mensagem de falha e redefine o status do bot.
        """

        try:
            # Regex para extrair nome, sobrenome e limite do formulário formatado
            padrao = r"\*Digite seu nome!\s*:\*\s*(.*?)\s*(?:\n|\r|\r\n)?\s*\*Digite seu sobrenome!\s*:\*\s*(.*?)\s*(?:\n|\r|\r\n)?\s*\*Qual seu limite de gastos mensal\?\s*:\*\s*([\d.,]+)"

            match = re.search(padrao, formulario)

            # Extração dos dados do regex
            nome = match.group(1).strip()
            sobrenome = match.group(2).strip()
            telefone = numero_telefone
            limite = int(match.group(3))
            
            # Prepara os dados para inserção no banco
            columns = ('nome', 'sobrenome', 'telefone', 'limite')
            placeholders = ', '.join(['%s'] * len(columns))
            values = (nome, sobrenome, telefone, limite)

            # Query de inserção
            create_usuario = (f"""INSERT INTO usuarios ({', '.join(columns)}) VALUES ({placeholders})""")

            # Executa a inserção no banco
            db.execute_script(create_usuario, values)

            # Envia mensagem de confirmação para o usuário
            waha.send_message(chatId, 'Seu cadastro foi concluido com sucesso! Agora você pode enviar seus gastos e despesas aqui, assim, irei armazenar todas as informaçoes para você e você terá o controle dos seus gastos de forma muito mais fácil :)')

        except Exception as e:
            print(f'Erro ao adicionar informações do usuário')
            print(e)
            # Em caso de erro, registra o erro e notifica o usuário
            waha.send_message(chatId, 'Ocorreu um erro ao cadastrar seu usuário, a equipe técnica irá analisar o ocorrido!')
            
            bot.define_status(chatId, 'start') # Redefine o status do bot para o início
            return