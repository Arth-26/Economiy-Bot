from flask import Flask, request, jsonify
from services.waha_bot import WahaBot
from services.database_functions import DataBase
from services.api_function import ApiClass
import utils, time
import re

app = Flask(__name__)

waha = WahaBot()
api_class = ApiClass()

conversation_state = api_class.get_conversation_state


@app.route('/economy_bot/webhook/', methods=['POST'])
def webhook():
    data = request.json
    chat_id = data['payload']['from']
    if re.search('\\@c\\b', chat_id, re.IGNORECASE):
        timestamp = data['payload']["timestamp"]

        if timestamp > waha.get_start_time:
            numero_telefone = utils.filtrar_digits(chat_id)
            message_content = data['payload']['body']
            #LEMBRAR DE TIRAR ESSA VERIFICAÇÃO
            if numero_telefone == '558398305769':
                if api_class.verificar_usuario(numero_telefone):
                    campo = api_class.prosseguir_cadastro(numero_telefone)
                    if campo == 'completo':
                        pass
                    else:
                        api_class.inserir_proximo_campo(campo, message_content, chat_id, numero_telefone)
                else:
                    state = api_class.define_status(chat_id)
                    if state == 'cadastro':
                        api_class.adicionar_usuario(numero_telefone)
                        api_class.inserir_proximo_campo('nome', message_content, chat_id, numero_telefone)
                    else:
                        api_class.define_proxima_mensagem(state, chat_id, message_content)
            else:
                return 'OK'
        else:
            return 'OK'


    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    print("⌛ Aguardando WAHA iniciar...")
    time.sleep(10) 
    waha.create_session_webhook()
    app.run(host='0.0.0.0', port=5000, debug=True)
    