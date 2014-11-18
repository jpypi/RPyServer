import sqlite3 as sql
from hashlib import sha1
from random import random
from time import time
from utils import timeFuture

hrs_2=2*60*60
day_1=86400

class SessionManager(sql.Connection):
    def __init__(self,db_name):
        sql.Connection.__init__(self,db_name)
        self.makeTables()

    def getSession(self,handler,cookies):
        return Session(handler,cookies,self)

    def makeTables(self):
        c=self.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS sessions (tag TEXT,expires REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS variables (session_rowid INTEGER,key TEXT,value TEXT,UNIQUE (session_rowid,key))")
        c.close()
        self.commit()

    def dropTables(self):
        c=self.cursor()
        c.execute("DROP TABLE sessions")
        c.execute("DROP TABLE variables")
        self.commit()
        c.close()

    def addSession(self,session):
        c=self.cursor()
        c.execute("INSERT INTO sessions VALUES (\"%s\",%s)"%(session.sid_tag,time()+hrs_2))
        self.commit()
        c.close()

        
        
class Session:
    def __init__(self,handler,cookies,session_manager):
        self.handler=handler
        self.cookies=cookies
        self.conn=session_manager

        #Get session id or initialize a new session cookie
        self.sid_tag=cookies.get("__sid",None)
        if not self.sid_tag:
            self.sid_tag=sha1(str(time()+random())).hexdigest()
            handler.SetCookie("__sid",self.sid_tag,path="/")
        self.rowid=self.tagToID()


    def tagToID(self):
        c=self.conn.cursor()
        c.execute("SELECT rowid FROM sessions WHERE tag=\"%s\" AND expires>%s"%(self.sid_tag,time()))
        res=c.fetchone()
        c.close()
        if not res:
            self.conn.addSession(self)
            c=self.conn.cursor()
            c.execute("SELECT rowid FROM sessions WHERE tag=\"%s\" AND expires>%s"%(self.sid_tag,time()))
            res=c.fetchone()
            c.close()
        return res[0]


    def end(self):
        self.conn.commit()


    def getValue(self,key):
        c=self.conn.cursor()
        c.execute("SELECT value FROM variables WHERE session_rowid=%s AND key=\"%s\""%(self.rowid,key))
        results=c.fetchone()
        c.close()
        if results:
            return results[0]
        else:
            return None

    def setValue(self,key,value):
        if type(key)==str and type(value)==str:
            c=self.conn.cursor()
            c.execute("INSERT OR REPLACE INTO variables VALUES (%d,\"%s\",\"%s\")"%(self.rowid,key,value))
            self.conn.commit()
            c.close()
        else:
            raise ValueError,"key and value must be strings!"


    def __getitem__(self,key):
        return self.getValue(key)


    def __setitem__(self,key,value):
        self.setValue(key,value)


    def destroy(self):
        c=self.conn.cursor()
        c.execute("DELETE FROM variables WHERE session_rowid=%d"%self.rowid)
        c.execute("DELETE FROM sessions WHERE rowid=%d"%self.rowid)
        c.close()
        self.conn.commit()
        self.handler.SetCookie("__sid","",path="/",expires=timeFuture(-42000))
        
