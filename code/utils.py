import re

def filtrar_digits(string):
    string = re.sub('[^0-9]', '', string)
    return string

def verificar_tipo_mensagem_recebida(message_data):
    temMedia = message_data['payload']['hasMedia']
    if temMedia:
        return 'media'
    return 'texto'

