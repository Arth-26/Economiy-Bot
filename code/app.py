import re
import time

from flask import Flask, jsonify, request
from models.usuarios import Usuarios
from services.bot_functions import BotClass
from services.llama_functions import LlamaClass
from services.waha import WahaBot
from utils import filtrar_digits, verificar_tipo_mensagem_recebida

app = Flask(__name__)

waha = WahaBot()
api_class = BotClass()
ai_bot = LlamaClass()
usuario = Usuarios()

conversation_state = api_class.get_conversation_state


@app.route('/economy_bot/webhook/', methods=['POST'])
def webhook():
    print('CHAMANDO WEBHOOK')
    data = request.json
    chat_id = data['payload']['from']
    if verificar_tipo_mensagem_recebida(data) == 'texto':
        if re.search('\\@c\\b', chat_id, re.IGNORECASE):
            timestamp = data['payload']["timestamp"]

            if timestamp > waha.get_start_time:
                numero_telefone = filtrar_digits(chat_id)
                message_content = data['payload']['body']
                #LEMBRAR DE TIRAR ESSA VERIFICAÇÃO
                if numero_telefone == '558398305769' or numero_telefone == '558399109114':
                    if usuario.verificar_usuario(numero_telefone):
                        ai_bot.identificar_função(chat_id, message_content)
                    else:
                        state = api_class.define_status(chat_id)
                        if state == 'cadastro':
                            if re.findall('Cadastro Economy Bot', message_content, re.IGNORECASE):
                                usuario.cadastrar_usuario(message_content, chat_id, numero_telefone)
                            else:
                                waha.send_message(chat_id, 'Mensagem de cadastro inválida! Por favor, responda o formulário para se cadastrar')
                        else:
                            api_class.define_proxima_mensagem(state, chat_id, message_content)
                else:
                    return 'OK'
            else:
                return 'OK'
    else:
        waha.send_message(chat_id, 'Formato de mensagem inválida! Por favor, envie apenas mensagens de texto!')

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    print("⌛ Aguardando WAHA iniciar...")
    time.sleep(10) 
    waha.create_session_webhook()
    app.run(host='0.0.0.0', port=5000, debug=True)
    