import os, sqlite3, hashlib
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.getenv('ICONNECT_DB_PATH', 'iconnect.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, company TEXT, email TEXT, phone TEXT, product TEXT,
            source TEXT, stage TEXT, score INTEGER, owner TEXT, value REAL DEFAULT 0,
            last_contact TEXT, next_followup TEXT, notes TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT UNIQUE NOT NULL,
            issue TEXT NOT NULL, priority TEXT, status TEXT, team TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, objective TEXT, audience TEXT, channel TEXT,
            start_date TEXT, budget REAL DEFAULT 0, status TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, campaign TEXT, channel TEXT, content TEXT,
            status TEXT, reviewer TEXT, scheduled_date TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, campaign TEXT, impressions INTEGER,
            clicks INTEGER, leads INTEGER, spend REAL
        );
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_time TEXT NOT NULL,
            lead_id TEXT, event TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_time TEXT NOT NULL, event TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer', password_hash TEXT NOT NULL, active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_time TEXT NOT NULL, username TEXT,
            action TEXT NOT NULL, entity TEXT, entity_id TEXT, details TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS consent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, channel TEXT, purpose TEXT NOT NULL,
            consent_status TEXT NOT NULL, source TEXT, recorded_by TEXT, recorded_at TEXT NOT NULL,
            withdrawn_at TEXT
        );
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT, workspace_key TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            active INTEGER DEFAULT 1, created_at TEXT NOT NULL
        );
        ''')
        if c.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0] == 0:
            c.execute('INSERT INTO workspaces(workspace_key,name,created_at) VALUES (?,?,?)',('default','iConnect SA Demo Workspace',datetime.now().isoformat(timespec='seconds')))
        if c.execute('SELECT COUNT(*) FROM leads').fetchone()[0] == 0:
            now=datetime.now().isoformat(timespec='seconds')
            seed=[('LEAD-1001','Thabo Mokoena','Mokoena Logistics','thabo@example.com','+27 82 555 0101','Business Internet','Website','Qualified',82,'Sales Team',18500,'2026-10-10','2026-10-13','Needs resilient connectivity for 3 branches.',now),('LEAD-1002','Naledi Dlamini','Dlamini Consulting','naledi@example.com','+27 71 555 0188','VoIP','WhatsApp','Contacted',64,'Sales Team',7200,'2026-10-08','2026-10-12','Interested in hosted business telephony.',now)]
            c.executemany('INSERT INTO leads(lead_id,name,company,email,phone,product,source,stage,score,owner,value,last_contact,next_followup,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',seed)
        if c.execute('SELECT COUNT(*) FROM campaigns').fetchone()[0] == 0:
            c.execute('INSERT INTO campaigns(campaign_id,name,objective,audience,channel,start_date,budget,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)',('CMP-001','Fibre Upgrade Awareness','Generate leads','SME customers','Email','2026-10-14',5000,'Draft',datetime.now().isoformat(timespec='seconds')))
        if c.execute('SELECT COUNT(*) FROM results').fetchone()[0] == 0:
            c.executemany('INSERT INTO results(campaign,impressions,clicks,leads,spend) VALUES (?,?,?,?,?)',[('Fibre Upgrade Awareness',12400,620,48,2100),('Connectivity Tips',8900,410,19,980)])

def rows(table, order='id DESC'):
    with db() as c: return [dict(x) for x in c.execute(f'SELECT * FROM {table} ORDER BY {order}').fetchall()]

def add_activity(event, lead_id=None):
    with db() as c: c.execute('INSERT INTO activity(event_time,lead_id,event) VALUES (?,?,?)',(datetime.now().isoformat(timespec='seconds'),lead_id,event))

def add_alert(event):
    with db() as c: c.execute('INSERT INTO alerts(event_time,event) VALUES (?,?)',(datetime.now().isoformat(timespec='seconds'),event))

def get_user(username):
    with db() as c:
        row=c.execute('SELECT * FROM users WHERE username=? AND active=1',(username,)).fetchone()
        return dict(row) if row else None

def ensure_admin(username, password):
    if not username or not password: return
    with db() as c:
        row=c.execute('SELECT id FROM users WHERE username=?',(username,)).fetchone()
        if row:
            c.execute('UPDATE users SET role="admin", password_hash=?, active=1 WHERE username=?',(hash_password(password),username))
        else:
            c.execute('INSERT INTO users(username,role,password_hash,active,created_at) VALUES (?,?,?,?,?)',(username,'admin',hash_password(password),1,datetime.now().isoformat(timespec='seconds')))

def add_audit(username, action, entity=None, entity_id=None, details=None):
    with db() as c:
        c.execute('INSERT INTO audit_log(event_time,username,action,entity,entity_id,details) VALUES (?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),username,action,entity,entity_id,details))

def setting(key, default=''):
    with db() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return row['value'] if row else default

def set_setting(key, value):
    with db() as c:
        c.execute('INSERT INTO settings(key,value,updated_at) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at',(key,value,datetime.now().isoformat(timespec='seconds')))
