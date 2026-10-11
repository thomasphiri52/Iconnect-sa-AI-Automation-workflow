import os, secrets
from fastapi import FastAPI, Request, HTTPException
from db import init_db, db, add_alert
app=FastAPI(title="iConnect SA Lead Webhook", version="3.0")
init_db()

@app.get("/health")
def health(): return {"status":"ok","service":"iconnect-webhook"}

@app.post("/webhook/lead")
async def lead(request: Request):
    token=os.getenv("ICONNECT_WEBHOOK_TOKEN","")
    if token and request.headers.get("x-iconnect-token") != token: raise HTTPException(401,"Invalid webhook token")
    data=await request.json(); name=(data.get("name") or "Website Lead").strip(); email=data.get("email",""); phone=data.get("phone",""); company=data.get("company",""); notes=data.get("message","")
    if not (email or phone): raise HTTPException(400,"email or phone is required")
    lead_id="WEB-"+secrets.token_hex(4).upper()
    from datetime import datetime
    with db() as c:
        c.execute("INSERT INTO leads(lead_id,name,company,email,phone,product,source,stage,score,owner,value,last_contact,next_followup,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(lead_id,name,company,email,phone,data.get("product","General"),"Website","New",40,"Unassigned",float(data.get("value",0) or 0),"—","—",notes,datetime.now().isoformat(timespec="seconds")))
    add_alert(f"New website lead {lead_id}")
    return {"ok":True,"lead_id":lead_id}
