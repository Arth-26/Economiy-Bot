import re

def filtrar_digits(string):
    string = re.sub('[^0-9]', '', string)

    return string