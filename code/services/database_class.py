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
        '''
            Função usada para executar Scripts sql, como Creates Updates e Inserts
        '''
        try:
            cur = self.__con.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            self.__con.commit()
        except Exception as e:
            print('ERRO AO EXECUTAR SCRIPT')
            print("Query:", sql)
            print(e)
            self.__con.rollback() 
            return False
        finally:
            cur.close()
        return True

    def execute_query(self, sql, params=None):
        '''
            Função usada para executar Querys sql, como consultas ao banco de dados
        '''
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
            self.__con.rollback()
            return []
        finally:
            cur.close()
        return rs

    def fechar(self):
        self.__con.close()


