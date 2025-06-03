import json
import re


def filtrar_digitos(string):
    string = re.sub('[^0-9]', '', string)
    return string

def verificar_tipo_mensagem_recebida(message_data):
    temMedia = message_data['payload']['hasMedia']
    if temMedia:
        return 'media'
    return 'texto'

def formatar_valor_brasileiro(valor):
    return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def ler_arquivo(arquivo, type):
    with open(arquivo, 'r', encoding='utf-8') as f:
        if type == 'text':
            arquivo = f.read()
        else:
            arquivo = json.load(f)
