import sqlite3

from config import DATABASE_PATH
from flask import g

def queryDB(query, args=(), one=False):
    cur = g.db.execute(query, args)
    ret = cur.fetchall()
    cur.close()
    if ret is not None and len(ret) > 0 and one:
        return ret[0]
    else:
        return ret

def alterDB(query, args=()):
    cur = g.db.execute(query, args)
    g.db.commit()
    id = cur.lastrowid
    cur.close()
    return id

def createDB():
    g.db = sqlite3.connect(DATABASE_PATH)

def destroyDB():
    if hasattr(g, 'db'):
        g.db.close()
