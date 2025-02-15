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
        waha_url = f"{self.__url}/api/sessions"

        for i in range(10):
            try:
                response = requests.get(waha_url)
                if response.status_code == 200:
                    print("✅ WAHA está pronto!")
                    return True
            except requests.ConnectionError:
                print(f"⏳ Aguardando WAHA... Tentativa {i+1}/10")
            time.sleep(2)  # Espera 2 segundos antes de tentar novamente

        print("❌ WAHA não está respondendo. Abortando...")
        return False
    
    def waha_initialize(self):
        waha_start_url = f'{self.__url}/api/sessions/default/start'

        try:
            response = requests.post(waha_start_url)
            
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
            response = requests.post(waha_stop_url)
            response = requests.put(waha_put_url, json=params)

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

        message_length = len(message)
        sleep_time = 1.5 if message_length < 20 else 2 if message_length < 50 else 3
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
            headers= headers
        )
