import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class DataBase:
    
    def __init__(self):
        self.__con = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'))

    def execute_script(self, sql):
        try:
            cur = self.__con.cursor()
            cur=self._db.cursor()
            cur.execute(sql)
            cur.close();
            self._db.commit()
        except:
            return False;
        return True;

    def execute_query(self, sql):
        rs=None
        try:
            cur=self.__con.cursor()
            cur.execute(sql)
            rs=cur.fetchall();
        except:
            return None
        return rs

    def fechar(self):
        self.__con.close()


