import os, random, hashlib, hmac
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from db import init_db, db, rows, add_activity, add_alert, get_user, ensure_admin, add_audit
from integrations import ai_generate

st.set_page_config(page_title="iConnect SA AI Automation", page_icon="🤖", layout="wide")
st.markdown("""<style>.stApp{background:linear-gradient(135deg,#080d1a,#101a32)} section[data-testid="stSidebar"]{background:#0b1224} div[data-testid="stMetric"]{background:#121c32;border:1px solid #263654;padding:14px;border-radius:12px}</style>""",unsafe_allow_html=True)

PAGES=["Overview","Lead / CRM","AI Customer Service","Ticket Queue","Alerts & Activity","Plan Campaigns","Generate Content","Schedule & Approvals","Report Results","Settings","Integrations","POPIA Consent"]
ROLE_PAGES={"viewer":["Overview","AI Customer Service","Ticket Queue","Alerts & Activity","Report Results"],"agent":["Overview","Lead / CRM","AI Customer Service","Ticket Queue","Alerts & Activity","Plan Campaigns","Generate Content","Schedule & Approvals","Report Results"],"manager":PAGES,"admin":PAGES}
STAGES=["New","Contacted","Qualified","Proposal","Won","Lost"]
PRODUCTS=["Fibre","Business Internet","VoIP","Cloud","Managed Services","General"]
SOURCES=["Website","WhatsApp","Email","Social","Campaign","Referral","Customer Service","Manual"]

def secret(name,default=""):
    try:
        v=st.secrets.get(name)
        if v is not None and str(v).strip(): return str(v)
    except Exception: pass
    return os.getenv(name,default)

@st.cache_resource
def boot():
    init_db(); return True
boot()
admin_user=secret("ICONNECT_ADMIN_USER","admin")
admin_password=secret("ICONNECT_ADMIN_PASSWORD","")
if admin_password: ensure_admin(admin_user,admin_password)

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def login():
    if st.session_state.get("auth"): return
    st.sidebar.title("🤖 iConnect SA")
    u=st.sidebar.text_input("Username")
    p=st.sidebar.text_input("Password",type="password")
    if st.sidebar.button("Sign in",type="primary"):
        a=get_user(u)
        if a and hmac.compare_digest(a["password_hash"],hash_pw(p)):
            st.session_state.update(auth=True,user=u,role=a["role"]); add_audit(u,"login"); st.rerun()
        else: st.sidebar.error("Invalid credentials")
    st.title("iConnect SA | Secure workspace")
    if not admin_password: st.error("Configure ICONNECT_ADMIN_USER and ICONNECT_ADMIN_PASSWORD in Streamlit Secrets, then reboot the app.")
    else: st.info("Sign in from the sidebar to continue.")
    st.stop()
login()

def data(name): return pd.DataFrame(rows(name))
def score(stage,product,source,value,contact):
    s=35+{"New":0,"Contacted":10,"Qualified":25,"Proposal":30,"Won":40,"Lost":-30}.get(stage,0)+{"Managed Services":15,"Business Internet":12,"Cloud":10,"Fibre":8,"VoIP":7}.get(product,0)+{"Referral":12,"WhatsApp":8,"Campaign":7,"Website":5}.get(source,0)+min(15,int(float(value or 0)/5000))+(5 if contact else 0)
    return max(0,min(100,s))
def classify(msg):
    m=msg.lower()
    for words,cat,priority,team in [(('down','outage','offline'),'Connectivity','High','Network Ops'),(('slow','latency'),'Connectivity','Medium','Network Ops'),(('voip','call','phone'),'Voice','High','Voice Support'),(('invoice','billing','payment'),'Billing','Low','Billing'),(('password','login'),'Account access','Medium','Service Desk')]:
        if any(w in m for w in words): return cat,priority,team
    return 'General enquiry','Medium','Service Desk'
def nav(target): st.session_state.page=target; st.rerun()

if "page" not in st.session_state: st.session_state.page="Overview"
st.sidebar.title("🤖 iConnect SA")
st.sidebar.caption(f"AI Automation Control Room · {st.session_state.get('user','admin')} · {st.session_state.get('role','viewer')}")
allowed=ROLE_PAGES.get(st.session_state.get("role","viewer"),ROLE_PAGES["viewer"])
st.session_state.page=st.sidebar.radio("Navigation",allowed,index=allowed.index(st.session_state.page) if st.session_state.page in allowed else 0)
if st.sidebar.button("Sign out"):
    add_audit(st.session_state.get("user"),"logout"); st.session_state.clear(); st.rerun()

st.title("iConnect SA | AI Automation")
st.caption("CRM · customer service · campaigns · approvals · reporting")
leads=data("leads"); tickets=data("tickets"); campaigns=data("campaigns"); results=data("results")

if st.session_state.page=="Overview":
    active=leads[~leads["stage"].isin(["Won","Lost"])] if not leads.empty else leads
    a,b,c,d,e=st.columns(5)
    a.metric("Open tickets",len(tickets[tickets["status"]!="Resolved"]) if not tickets.empty else 0)
    b.metric("Active leads",len(active))
    c.metric("Qualified leads",len(leads[leads["stage"].isin(["Qualified","Proposal"])]) if not leads.empty else 0)
    pipeline=float(active["value"].sum()) if not active.empty else 0
    d.metric("Pipeline value",f"R{pipeline:,.0f}")
    reported=int(results["leads"].sum()) if not results.empty else 0
    e.metric("Reported leads",reported)
    st.subheader("Quick actions")
    for col,label,target in zip(st.columns(5),["👥 Open CRM","🎧 Customer Service","🎫 Ticket Queue","📣 Plan Campaign","📊 Reports"],["Lead / CRM","AI Customer Service","Ticket Queue","Plan Campaigns","Report Results"]):
        if col.button(label,use_container_width=True): nav(target)
    l,r=st.columns(2)
    with l:
        st.subheader("Lead pipeline")
        if not leads.empty: st.bar_chart(leads["stage"].value_counts().reindex(STAGES,fill_value=0))
    with r:
        st.subheader("Pipeline value")
        if not leads.empty: st.bar_chart(leads.groupby("stage")["value"].sum())
    st.subheader("Campaign results")
    st.dataframe(results,use_container_width=True,hide_index=True)

elif st.session_state.page=="Lead / CRM":
    st.subheader("Lead & CRM Control Room")
    st.dataframe(leads,use_container_width=True,hide_index=True)
    with st.form("newlead"):
        c1,c2=st.columns(2); name=c1.text_input("Contact name *"); company=c2.text_input("Company"); email=c1.text_input("Email"); phone=c2.text_input("Phone / WhatsApp"); product=c1.selectbox("Product",PRODUCTS); source=c2.selectbox("Source",SOURCES); stage=c1.selectbox("Stage",STAGES); owner=c2.text_input("Owner","Sales Team"); value=c1.number_input("Deal value (R)",min_value=0.0,step=500.0); notes=st.text_area("Notes"); ok=st.form_submit_button("Create lead",type="primary")
    if ok:
        if not name.strip() or not(email.strip() or phone.strip()): st.error("Name and email/phone are required.")
        else:
            lid=f"LEAD-{random.randint(1000,9999)}"; now=datetime.now().isoformat(timespec="seconds"); sc=score(stage,product,source,value,bool(email or phone))
            with db() as c: c.execute("INSERT INTO leads(lead_id,name,company,email,phone,product,source,stage,score,owner,value,last_contact,next_followup,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(lid,name,company,email,phone,product,source,stage,sc,owner,value,"—",str(date.today()+timedelta(days=2)),notes,now))
            add_activity("Lead created",lid); st.success(f"{lid} created with score {sc}/100"); st.rerun()

elif st.session_state.page=="AI Customer Service":
    st.subheader("AI Customer Service")
    msg=st.text_area("Customer message")
    if st.button("Analyse enquiry",type="primary") and msg.strip(): st.session_state.triage=classify(msg)
    if "triage" in st.session_state:
        cat,priority,team=st.session_state.triage; a,b,c=st.columns(3); a.metric("Category",cat); b.metric("Priority",priority); c.metric("Team",team)
        st.text_area("Suggested reply",f"Thanks for contacting iConnect SA. Our {team} team will review your {cat.lower()} enquiry. Never send passwords or OTPs.")
        if st.button("Create ticket & alert",type="primary"):
            tid=f"IC-{random.randint(2000,9999)}"
            with db() as c: c.execute("INSERT INTO tickets(ticket_id,issue,priority,status,team,created_at) VALUES (?,?,?,?,?,?)",(tid,msg,priority,"Open",team,datetime.now().isoformat(timespec="seconds")))
            add_alert(f"{tid} routed to {team}"); st.success(f"{tid} created"); st.rerun()

elif st.session_state.page=="Ticket Queue":
    st.subheader("Ticket Queue"); t=data("tickets"); st.dataframe(t,use_container_width=True,hide_index=True)
    if not t.empty:
        tid=st.selectbox("Ticket",t["ticket_id"].tolist()); status=st.selectbox("Status",["Open","In progress","Resolved"])
        if st.button("Update ticket"):
            with db() as c: c.execute("UPDATE tickets SET status=? WHERE ticket_id=?",(status,tid))
            add_alert(f"{tid} status changed to {status}"); st.rerun()

elif st.session_state.page=="Alerts & Activity":
    st.subheader("Alerts"); st.dataframe(data("alerts"),use_container_width=True,hide_index=True); st.subheader("Activity"); st.dataframe(data("activity"),use_container_width=True,hide_index=True)

elif st.session_state.page=="Plan Campaigns":
    st.subheader("Campaign Planner")
    with st.form("campaign"):
        name=st.text_input("Campaign name"); objective=st.selectbox("Objective",["Generate leads","Awareness","Conversions","Engagement","Retention"]); audience=st.text_input("Target audience"); channel=st.selectbox("Channel",["Email","Social","SMS","Website","Multi-channel"]); budget=st.number_input("Budget (R)",min_value=0.0,step=500.0); ok=st.form_submit_button("Create campaign",type="primary")
    if ok and name.strip() and audience.strip():
        cid=f"CMP-{random.randint(100,999)}"
        with db() as c: c.execute("INSERT INTO campaigns(campaign_id,name,objective,audience,channel,start_date,budget,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(cid,name,objective,audience,channel,str(date.today()+timedelta(days=7)),budget,"Draft",datetime.now().isoformat(timespec="seconds")))
        add_alert(f"Campaign {cid} created"); st.success(f"{cid} created"); st.rerun()
    st.dataframe(data("campaigns"),use_container_width=True,hide_index=True)

elif st.session_state.page=="Generate Content":
    st.subheader("AI Content Generator"); c=data("campaigns")
    if c.empty: st.info("Create a campaign first.")
    else:
        campaign=st.selectbox("Campaign",c["name"].tolist()); audience=st.text_input("Audience","iConnect SA customers"); objective=st.selectbox("Objective",["Generate leads","Awareness","Conversions","Engagement"]); tone=st.selectbox("Tone",["Professional","Friendly","Helpful","Energetic"])
        if st.button("Generate draft",type="primary"): st.session_state.generated=ai_generate(f"Create professional marketing content for {audience}. Objective: {objective}. Tone: {tone}. Campaign: {campaign}.")
        if "generated" in st.session_state:
            st.text_area("Draft",st.session_state.generated,height=260)

elif st.session_state.page=="Schedule & Approvals":
    st.subheader("Schedule & Approvals"); a=data("approvals"); st.dataframe(a,use_container_width=True,hide_index=True)
    if not a.empty: st.info("Pending content can be reviewed and scheduled from the approval workflow.")

elif st.session_state.page=="Report Results":
    st.subheader("Campaign Reporting"); st.dataframe(results,use_container_width=True,hide_index=True)
    if not results.empty:
        total_leads=int(results["leads"].sum()); total_spend=float(results["spend"].sum()); a,b=st.columns(2); a.metric("Total leads",total_leads); b.metric("Total spend",f"R{total_spend:,.0f}"); st.bar_chart(results.set_index("campaign")["leads"])

elif st.session_state.page=="Settings":
    st.subheader("Settings"); st.success("Authentication is enabled."); st.write({"Admin user":admin_user,"Role":st.session_state.get("role"),"Database":"SQLite / PostgreSQL-ready"})

elif st.session_state.page=="Integrations":
    st.subheader("Integration Status")
    st.write({"AI provider":"Configured" if secret("OPENAI_API_KEY") else "Not configured","WhatsApp":"Configured" if secret("WHATSAPP_ACCESS_TOKEN") and secret("WHATSAPP_PHONE_NUMBER_ID") else "Not configured","SMTP":"Configured" if secret("SMTP_HOST") else "Not configured","Lead webhook":"Available via webhook.py"})
    st.info("Keep credentials in Streamlit Secrets. Never commit secrets to GitHub.")

elif st.session_state.page=="POPIA Consent":
    st.subheader("POPIA Consent Register"); st.dataframe(data("consent_log"),use_container_width=True,hide_index=True)
    with st.form("consent"):
        subject=st.text_input("Subject / customer"); purpose=st.text_input("Purpose"); status=st.selectbox("Consent status",["Granted","Withdrawn","Pending"]); ok=st.form_submit_button("Record consent",type="primary")
    if ok and subject.strip() and purpose.strip():
        with db() as c: c.execute("INSERT INTO consent_log(subject,channel,purpose,consent_status,source,recorded_by,recorded_at) VALUES (?,?,?,?,?,?,?)",(subject,"",purpose,status,"Dashboard",st.session_state.get("user"),datetime.now().isoformat(timespec="seconds")))
        st.success("Consent record saved."); st.rerun()
