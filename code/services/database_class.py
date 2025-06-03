import os

import psycopg2
from psycopg2 import DataError
from dotenv import load_dotenv

load_dotenv()

class DataBase:
    
    def __init__(self):
        self.__con = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'))

    def execute_script(self, sql, params=None):
        try:
            cur = self.__con.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            cur.close()
            self.__con.commit()
        except DataError as e:
            print('ERRO AO EXECUTAR SCRIPT')
            print(e)
            cur.close()
            return False
        except Exception as e:
            print('ERRO AO EXECUTAR SCRIPT')
            print("Query:", sql)
            print(e)
            cur.close()
            return False
        return True

    def execute_query(self, sql, params=None):
        rs=None
        try:
            cur=self.__con.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            rs=cur.fetchall()
        except Exception as e:
            print('ERRO AO EXECUTAR QUERY')
            print("Query:", sql)
            print(e)
            cur.close()
            return []
        return rs

    def fechar(self):
        self.__con.close()


