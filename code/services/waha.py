import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class WahaBot:

    def __init__(self):
        self.__url = 'http://waha:3000'
        self.__start_time = int(datetime.now().timestamp())
        self.__my_chat_id = str(os.getenv('MY_CHAT_ID'))

    @property
    def get_start_time(self):
        return self.__start_time
    
    """FUNÇÕES DE INICIALIZAÇÃO, EXECUTADAS AO INICIAR O SISTEMA"""

    def wait_for_waha(self):
        '''
            Função feita para servir como um timeout para a inicialização do sistema waha.
            Caso não inicializa após algum tempo, encerra a inicialização
        '''
        waha_url = f"{self.__url}/api/sessions"

        for i in range(10):
            try:
                response = requests.get(waha_url, timeout=10)
                if response.status_code == 200:
                    print("✅ WAHA está pronto!")
                    return True
            except requests.ConnectionError:
                print(f"⏳ Aguardando WAHA... Tentativa {i+1}/10")
            time.sleep(2)  # Espera 2 segundos antes de tentar novamente

        print("❌ WAHA não está respondendo. Abortando...")
        return False
    
    def waha_initialize(self):
        '''
            Cria e inicializa o webhook da sessão para o funcionamento do sistema
            Caso o webhook não seja criado corretamente, o sistema não irá funcionar
        '''
        waha_start_url = f'{self.__url}/api/sessions/default/start'

        try:
            response = requests.post(waha_start_url, timeout=10)
            
            if response.status_code in [200, 201]:
                print("Webhook registrado com sucesso!")
            else:
                print(f"❌ Erro ao registrar webhook!")
                print(f"🔹 Status Code: {response.status_code}")
                print(f"🔹 Response Text: {response.text}")
        except Exception as e:
            print('Erro na inicialização do waha ------------------')
            print(e)

    def create_session_webhook(self):

        '''
            Cria a sessão do webhook para ativar junto com o app Flask, onde todos os comandos serão executados
        '''
        if not self.wait_for_waha():
            return 

        waha_stop_url = f'{self.__url}/api/sessions/default/stop'
        waha_put_url = f'{self.__url}/api/sessions/default'
        webhook_url = "http://api:5000/economy_bot/webhook/"

        params = {
            "config": {
                "webhooks": [
                    {
                        "url": webhook_url,
                        "events": [
                            "message"
                        ],
                        "hmac": None,
                        "retries": None,
                        "customHeaders": None
                    }
                ]
            }
        }

        try:
            response = requests.post(waha_stop_url, timeout=10)
            response = requests.put(waha_put_url, json=params, timeout=10)

            if response.status_code == 200:
                print("Webhooks atualizados com sucesso!")
                self.waha_initialize()
            else:
                print(f"Erro ao atualizar webhooks: {response.text}")
        except Exception as e:
            print('Erro na criação de webhook')
            print(e)
        

    """FUNÇÕES DE CHAMADA DA API WAHA"""

    def send_message(self, chatId, message):
        ''' 
            Função para enviar mensagem para o usuário
            Essa função é a base de todo o sistema, usada para enviar todas as mensagens para o usuário 
            seguindo o fluxo de funcionamento do sistema
        '''

        # Verifica o tamanho da mensagem que será enviada para definir quando tempo irá demorar para enviar a mensagem
        # Assim, evita que o bot responda automaticamente e tenha problemas com a plataforma Whatsapp
        message_length = len(message) 
        sleep_time = 1 if message_length < 50 else 2
        time.sleep(sleep_time)

        url = f'{self.__url}/api/sendText'
        headers = {
            'Content-Type': 'application/json',
        }

        payload = {
            "chatId": chatId,
            "text": message,
            "session": "default"
        }

        requests.post(
            url= url,
            json= payload,
            headers= headers,
            timeout=10
        )