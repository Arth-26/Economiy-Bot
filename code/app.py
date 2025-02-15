from flask import Flask, request, jsonify
from services.waha_bot import WahaBot
from services.database_functions import DataBase
from services.api_function import ApiClass
import utils, time

app = Flask(__name__)

db = DataBase()
waha = WahaBot()
api_class = ApiClass()

conversation_state = api_class.get_conversation_state


@app.route('/economy_bot/webhook/', methods=['POST'])
def webhook():
    data = request.json

    timestamp = data['payload']["timestamp"]

    if timestamp > waha.get_start_time:
        chat_id = data['payload']['from']
        numero_telefone = utils.filtrar_digits(chat_id)
        message_content = data['payload']['body']

        #LEMBRAR DE TIRAR ESSA VERIFICAÇÃO
        if numero_telefone == '558398305769':
            if api_class.verificar_usuario(numero_telefone):
                pass
            else:
                state = api_class.define_status(chat_id)
                if state == 'cadastro':
                    pass
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
    