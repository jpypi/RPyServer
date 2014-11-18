import sqlite3 as sql
import time
from hashlib import sha1

class ChatDB(sql.Connection):
    def __init__(self,db_name):
        sql.Connection.__init__(self,db_name)
        self.MakeTables()

    def MakeTables(self):
        c=self.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT,login_un TEXT,password TEXT,priviledges INTEGER,last_seen REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS chat_messages (user_id INTEGER,message TEXT,time REAL, chat_room INTEGER)")
        c.close()

    def DropTables(self):
        c=self.cursor()
        c.execute("DROP TABLE users")
        c.execute("DROP TABLE chat_messages")
        c.close()

    def AddMessage(self,user_id,message):
        c=self.cursor()
        c.execute("INSERT INTO chat_messages VALUES (%s,\"%s\",%.6f,0)"%(user_id,message,time.time()))
        c.close()

    def GetMessages(self,last_update_time):
        c=self.cursor()
        c.execute("SELECT chat_messages.time, users.name, chat_messages.message FROM chat_messages INNER JOIN users ON chat_messages.user_id=users.rowid WHERE time>%.6f ORDER BY time ASC"%last_update_time)
        res=c.fetchall()
        c.close()
        return res

    def AddUser(self,name,login,password,priviledges=0):
        c=self.cursor()
        c.execute("INSERT INTO users VALUES (\"%s\",\"%s\",\"%s\",'%s','0.0')"%(name,login,sha1(password).hexdigest(),priviledges))
        c.close()

if __name__=="__main__":
    c=ChatDB("test.db")
    c.commit()
