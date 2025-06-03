import json
import re


def filtrar_digitos(string):
    '''
        Filtra o chatID da mensagem enviada para retornar apenas seu número de telefone do usuário

        string - ChatId do usuário
    '''
    string = re.sub('[^0-9]', '', string)
    return string


def verificar_tipo_mensagem_recebida(message_data):
    '''
        Verifica tipo de mensagem recebida, confirmando se foi apenas texto ou se possui arquivos de midia

        message_data - Response Json das informações da mensagem enviada pelo usuário
    '''
    temMedia = message_data['payload']['hasMedia']
    if temMedia:
        return 'media'
    return 'texto'

def formatar_valor_brasileiro(valor):
    ''' 
        Formata valores monetários internacionais para o formato brasileiro 

        valor - Valor no formato americano
    '''
    return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def ler_arquivo(arquivo, type):
    ''' 
        Responsável pela leitura de arquivos 

        arquivo - path do arquivo que será lido
        type - Tipo do arquivo
    '''
    with open(arquivo, 'r', encoding='utf-8') as f:
        if type == 'text':
            arquivo = f.read()
        else:
            arquivo = json.load(f)
    return arquivo