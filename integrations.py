import os, requests
from email.message import EmailMessage
import smtplib


def ai_generate(prompt: str) -> str:
    """Provider adapter. Uses OpenAI-compatible endpoint when configured; otherwise returns a safe local draft."""
    key=os.getenv("OPENAI_API_KEY","")
    if not key:
        return "AI provider not configured. Draft locally or configure OPENAI_API_KEY on the server.\n\nPrompt:\n"+prompt
    model=os.getenv("OPENAI_MODEL","gpt-4o-mini")
    r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.4},timeout=30)
    r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]


def send_whatsapp(to: str, body: str) -> dict:
    token=os.getenv("WHATSAPP_ACCESS_TOKEN",""); phone_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID","")
    if not token or not phone_id: return {"ok":False,"error":"WhatsApp credentials are not configured."}
    url=f"https://graph.facebook.com/v23.0/{phone_id}/messages"
    r=requests.post(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},json={"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":body}},timeout=30)
    return {"ok":r.ok,"status":r.status_code,"response":r.json() if r.content else {}}


def send_email(to: str, subject: str, body: str) -> dict:
    host=os.getenv("SMTP_HOST",""); user=os.getenv("SMTP_USER",""); password=os.getenv("SMTP_PASSWORD","")
    if not host: return {"ok":False,"error":"SMTP credentials are not configured."}
    msg=EmailMessage(); msg["From"]=os.getenv("SMTP_FROM",user); msg["To"]=to; msg["Subject"]=subject; msg.set_content(body)
    with smtplib.SMTP(host,int(os.getenv("SMTP_PORT","587")),timeout=30) as s:
        s.starttls();
        if user: s.login(user,password)
        s.send_message(msg)
    return {"ok":True}
