import re
import time

from flask import Flask, jsonify, request
from models.usuarios import Usuarios
from services.bot_class import BotClass
from services.llama_class import LlamaClass
from services.waha import WahaBot
from utils import filtrar_digitos, verificar_tipo_mensagem_recebida

app = Flask(__name__)

waha = WahaBot()
api_class = BotClass()
ai_bot = LlamaClass()
usuario = Usuarios()

''' 
    FUNÇÃO PRINCIPAL, RESPONSÁVEL POR EXECUTAR TODO O RESTANDO DO CÓDIGO 
    A CADA MENSAGEM ENVIADA PELO USUÁRIO

    data - Informações no formato Json da mensagem enviada pelo usuário
    chat_id - Identificador do chat onde foi enviado a mensagem, contém o número de telefone do usuário
    timestamp - Momento em que a mensagem foi enviada no formato timestamp
    numero_telefone - Número de telefone do usuário
    message_content - Conteúdo da mensagem
    state - Estado de conversa de novos usuários
'''
@app.route('/economy_bot/webhook/', methods=['POST'])
def webhook():
    print('CHAMANDO WEBHOOK')
    data = request.json
    chat_id = data['payload']['from']
    
    if re.search('\\@c\\b', chat_id, re.IGNORECASE):
        timestamp = data['payload']["timestamp"]

        if timestamp > waha.get_start_time:
            numero_telefone = filtrar_digitos(chat_id)
            message_content = data['payload']['body']
            if verificar_tipo_mensagem_recebida(data) == 'texto':
                if usuario.verificar_usuario(numero_telefone): # Verifica se o usuário ja está cadastrado no sistema
                    ai_bot.executa_funcao(chat_id, message_content)
                else:
                    state = api_class.define_status(chat_id) # Caso não esteja, verifica o status de conversa com o usuário
                    if state == 'cadastro': # Se o status for cadastro, captura a mensagem de cadastro do usuário para filtrar os dados
                        if re.findall('Cadastro Economy Bot', message_content, re.IGNORECASE):
                            usuario.cadastrar_usuario(message_content, chat_id, numero_telefone)
                        else: # Caso não seja uma mensagem de cadastro na etapa de cadastro, retorna mensagem de aviso ao usuário
                            waha.send_message(chat_id, 'Mensagem de cadastro inválida! Por favor, responda o formulário para se cadastrar')
                    else: # Caso o status não seja de cadastro, verifica a proxima mensagem a ser enviada para o usuário baseado no status
                        api_class.define_proxima_mensagem(state, chat_id, message_content)
            else:
                waha.send_message(chat_id, 'Formato de mensagem inválida! Por favor, envie apenas mensagens de texto!')
           
        else:
            return 'OK'

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    '''
        Comandos executados ao iniciar o serviço do app usando Flask

        A função create_session_webhook é fundamental para a inicialização do sistema
    '''
    print("⌛ Aguardando WAHA iniciar...")
    time.sleep(10) 
    waha.create_session_webhook()
    app.run(host='0.0.0.0', port=5000, debug=True)
    