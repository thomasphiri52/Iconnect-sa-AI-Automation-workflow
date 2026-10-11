import os, random, hashlib, hmac
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from db import init_db, db, rows, add_activity, add_alert, get_user, ensure_admin, add_audit
from integrations import ai_generate, send_email, send_whatsapp

st.set_page_config(page_title="iConnect SA AI Automation", page_icon="🤖", layout="wide")
st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#080d1a,#101a32)}
section[data-testid="stSidebar"]{background:#0b1224}
div[data-testid="stMetric"]{background:#121c32;border:1px solid #263654;padding:14px;border-radius:12px}
</style>""", unsafe_allow_html=True)

LEAD_STAGES=["New","Contacted","Qualified","Proposal","Won","Lost"]
LEAD_SOURCES=["Website","WhatsApp","Email","Social","Campaign","Referral","Customer Service","Manual"]
PRODUCTS=["Fibre","Business Internet","VoIP","Cloud","Managed Services","General"]
PAGES=["Overview","Lead / CRM","AI Customer Service","Ticket Queue","Alerts & Activity","Plan Campaigns","Generate Content","Schedule & Approvals","Report Results","Settings","Integrations","POPIA Consent"]
ROLE_PAGES={"viewer":["Overview","AI Customer Service","Ticket Queue","Alerts & Activity","Report Results"],"agent":["Overview","Lead / CRM","AI Customer Service","Ticket Queue","Alerts & Activity","Plan Campaigns","Generate Content","Schedule & Approvals","Report Results"],"manager":PAGES,"admin":PAGES}

def secret(name, default=""):
    try:
        value=st.secrets.get(name)
        if value is not None and str(value).strip():
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

@st.cache_resource
def boot():
    init_db()
    return True
boot()

admin_user=secret("ICONNECT_ADMIN_USER", "admin")
admin_password=secret("ICONNECT_ADMIN_PASSWORD", "")
if admin_password:
    ensure_admin(admin_user, admin_password)

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate():
    if st.session_state.get("auth"):
        return True
    st.sidebar.title("🤖 iConnect SA")
    st.sidebar.caption("Secure workspace login")
    user=st.sidebar.text_input("Username")
    pw=st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Sign in", type="primary"):
        account=get_user(user)
        if account and hmac.compare_digest(account["password_hash"], hash_pw(pw)):
            st.session_state.auth=True
            st.session_state.user=user
            st.session_state.role=account["role"]
            add_audit(user,"login")
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials.")
    st.title("iConnect SA | Secure workspace")
    if not admin_password:
        st.error("Admin login is not configured. Add ICONNECT_ADMIN_USER and ICONNECT_ADMIN_PASSWORD to Streamlit Secrets, then reboot the app.")
    else:
        st.info("Sign in from the sidebar to continue.")
    st.stop()

authenticate()

def df(table):
    return pd.DataFrame(rows(table))

def lead_score(stage, product, source, value, has_contact):
    score=35+{"New":0,"Contacted":10,"Qualified":25,"Proposal":30,"Won":40,"Lost":-30}.get(stage,0)
    score+={"Business Internet":12,"Managed Services":15,"Cloud":10,"Fibre":8,"VoIP":7}.get(product,0)
    score+={"Referral":12,"WhatsApp":8,"Campaign":7,"Website":5,"Customer Service":5}.get(source,0)
    score+=min(15,int(float(value or 0)/5000))+(5 if has_contact else 0)
    return max(0,min(100,score))

def classify(message):
    text=message.lower()
    rules=[(("down","outage","offline"),"Connectivity","High","Network Ops"),(("slow","latency"),"Connectivity","Medium","Network Ops"),(("voip","call","phone"),"Voice","High","Voice Support"),(("invoice","billing","payment"),"Billing","Low","Billing"),(("password","login"),"Account access","Medium","Service Desk")]
    for words,category,priority,team in rules:
        if any(word in text for word in words):
            return category,priority,team
    return "General enquiry","Medium","Service Desk"

def makecopy(channel,audience,objective,offer,tone):
    extra=(" "+offer) if offer else ""
    if channel=="Email":
        return f"Subject: Stay connected with iConnect SA\n\nHi there,\nDiscover solutions designed for {audience}. Objective: {objective}.{extra}\nContact our team to explore your options.\n\nThe iConnect SA Team"
    if channel=="Social":
        return f"Stay connected. Keep moving! For {audience}, discover solutions built around the way you work.{extra} Contact iConnect SA. #iConnectSA"
    if channel=="SMS":
        return f"iConnect SA: {offer or 'Explore connectivity options built for you.'} Contact our team. Reply STOP to opt out."
    return f"Campaign brief\nAudience: {audience}\nObjective: {objective}\nMessage: Stay connected with iConnect SA.{extra}\nTone: {tone}\nCTA: Contact our team."

def navigate(target):
    st.session_state.page=target
    st.rerun()

if "page" not in st.session_state:
    st.session_state.page="Overview"
st.sidebar.title("🤖 iConnect SA")
st.sidebar.caption(f"AI Automation Control Room · {st.session_state.get('user','admin')} · {st.session_state.get('role','viewer')}")
allowed=ROLE_PAGES.get(st.session_state.get("role","viewer"), ROLE_PAGES["viewer"])
page=st.sidebar.radio("Navigation", allowed, index=allowed.index(st.session_state.page) if st.session_state.page in allowed else 0)
st.session_state.page=page
if st.sidebar.button("Sign out"):
    add_audit(st.session_state.get("user"),"logout")
    st.session_state.clear()
    st.rerun()

st.title("iConnect SA | AI Automation")
st.caption("CRM · customer service · campaigns · approvals · reporting")
leads=df("leads"); campaigns=df("campaigns"); tickets=df("tickets"); results=df("results")

if page=="Overview":
    active=leads[~leads["stage"].isin(["Won","Lost"])] if not leads.empty else leads
    a,b,c,d,e=st.columns(5)
    a.metric("Open tickets", len(tickets[tickets["status"]!="Resolved"]) if not tickets.empty else 0)
    b.metric("Active leads", len(active))
    c.metric("Qualified leads", len(leads[leads["stage"].isin(["Qualified","Proposal"])]) if not leads.empty else 0)
    d.metric("Pipeline value", f"R{active["value"].sum():,.0f}" if not active.empty else "R0")
    e.metric("Reported leads", int(results["leads"].sum()) if not results.empty else 0)
    st.subheader("Quick actions")
    cols=st.columns(5)
    for col,label,target in zip(cols,["👥 Open CRM","🎧 Customer Service","🎫 Ticket Queue","📣 Plan Campaign","📊 Reports"],["Lead / CRM","AI Customer Service","Ticket Queue","Plan Campaigns","Report Results"]):
        if col.button(label,use_container_width=True): navigate(target)
    l,r=st.columns(2)
    with l:
        st.subheader("Lead pipeline")
        if not leads.empty:
            chart=leads["stage"].value_counts().reindex(LEAD_STAGES,fill_value=0)
            st.bar_chart(chart)
    with r:
        st.subheader("Pipeline value")
        if not leads.empty:
            st.bar_chart(leads.groupby("stage")["value"].sum())
    st.subheader("Campaign results")
    st.dataframe(results,use_container_width=True,hide_index=True)

elif page=="Lead / CRM":
    st.subheader("Lead & CRM Control Room")
    tabs=st.tabs(["Pipeline","Add lead","Lead details","Activity & export"])
    with tabs[0]:
        st.dataframe(leads,use_container_width=True,hide_index=True)
    with tabs[1]:
        with st.form("addlead"):
            c1,c2=st.columns(2)
            name=c1.text_input("Contact name *"); company=c2.text_input("Company")
            email=c1.text_input("Email"); phone=c2.text_input("Phone / WhatsApp")
            product=c1.selectbox("Product",PRODUCTS); source=c2.selectbox("Source",LEAD_SOURCES)
            stage=c1.selectbox("Stage",LEAD_STAGES); owner=c2.text_input("Owner","Sales Team")
            value=c1.number_input("Deal value (R)",min_value=0.0,step=500.0)
            follow=c2.date_input("Next follow-up",date.today()+timedelta(days=2),min_value=date.today())
            notes=st.text_area("Notes"); ok=st.form_submit_button("Create lead",type="primary")
        if ok:
            if not name.strip() or not(email.strip() or phone.strip()):
                st.error("Name and email/phone are required.")
            else:
                lid=f"LEAD-{random.randint(1000,9999)}"; score=lead_score(stage,product,source,value,bool(email or phone)); now=datetime.now().isoformat(timespec="seconds")
                with db() as c:
                    c.execute("INSERT INTO leads(lead_id,name,company,email,phone,product,source,stage,score,owner,value,last_contact,next_followup,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(lid,name,company,email,phone,product,source,stage,score,owner,value,str(date.today()) if stage!="New" else "—",str(follow),notes,now))
                add_activity("Lead created",lid); st.success(f"{lid} created with score {score}/100."); st.rerun()
    with tabs[2]:
        if leads.empty: st.info("No leads yet.")
        else:
            sel=st.selectbox("Select lead",leads["lead_id"].tolist()); row=leads[leads["lead_id"]==sel].iloc[0]
            with st.form("editlead"):
                ns=st.selectbox("Stage",LEAD_STAGES,index=LEAD_STAGES.index(row.stage)); no=st.text_input("Owner",row.owner)
                nv=st.number_input("Value (R)",min_value=0.0,value=float(row.value),step=500.0); nn=st.text_area("Notes",row.notes)
                save=st.form_submit_button("Save changes",type="primary")
            if save:
                score=lead_score(ns,row.product,row.source,nv,bool(row.email or row.phone))
                with db() as c: c.execute("UPDATE leads SET stage=?,owner=?,value=?,notes=?,score=? WHERE id=?",(ns,no,nv,nn,score,int(row.id)))
                add_activity(f"Lead updated to {ns}",sel); st.success("Lead updated."); st.rerun()
    with tabs[3]:
        st.dataframe(df("activity"),use_container_width=True,hide_index=True)
        st.download_button("Download CRM CSV",leads.to_csv(index=False).encode(),"iconnect_crm_leads.csv","text/csv")

elif page=="AI Customer Service":
    st.subheader("AI Customer Service")
    msg=st.text_area("Customer message")
    if st.button("Analyse enquiry",type="primary") and msg.strip():
        st.session_state.triage={"msg":msg,"result":classify(msg)}
    if "triage" in st.session_state:
        category,priority,team=st.session_state.triage["result"]
        a,b,c=st.columns(3); a.metric("Category",category); b.metric("Priority",priority); c.metric("Team",team)
        st.text_area("Suggested reply",f"Thanks for contacting iConnect SA. Our {team} team will review your {category.lower()} enquiry. Never send passwords or OTPs.")
        if st.button("Create ticket & alert",type="primary"):
            tid=f"IC-{random.randint(2000,9999)}"
            with db() as c: c.execute("INSERT INTO tickets(ticket_id,issue,priority,status,team,created_at) VALUES (?,?,?,?,?,?)",(tid,msg,priority,"Open",team,datetime.now().isoformat(timespec="seconds")))
            add_alert(f"{tid} routed to {team}"); st.success(f"{tid} created and routed to {team}."); st.rerun()

elif page=="Ticket Queue":
    st.subheader("Ticket Queue"); st.dataframe(df("tickets"),use_container_width=True,hide_index=True)
    data=df("tickets")
    if not data.empty:
        tid=st.selectbox("Ticket",data["ticket_id"].tolist()); new=st.selectbox("Update status",["Open","In progress","Resolved"])
        if st.button("Update ticket"):
            with db() as c: c.execute("UPDATE tickets SET status=? WHERE ticket_id=?",(new,tid))
            add_alert(f"{tid} status changed to {new}"); st.rerun()

elif page=="Alerts & Activity":
    st.subheader("Alerts"); st.dataframe(df("alerts"),use_container_width=True,hide_index=True)
    st.subheader("CRM activity"); st.dataframe(df("activity"),use_container_width=True,hide_index=True)

elif page=="Plan Campaigns":
    with st.form("campaign"):
        name=st.text_input("Campaign name"); obj=st.selectbox("Objective",["Generate leads","Awareness","Conversions","Engagement","Retention"]); aud=st.text_input("Target audience")
        ch=st.selectbox("Channel",["Email","Social","SMS","Website","Multi-channel"]); start=st.date_input("Start date",date.today()+timedelta(days=7),min_value=date.today()); budget=st.number_input("Budget (R)",min_value=0.0,step=500.0); ok=st.form_submit_button("Create campaign",type="primary")
    if ok:
        if name.strip() and aud.strip():
            cid=f"CMP-{random.randint(100,999)}"
            with db() as c: c.execute("INSERT INTO campaigns(campaign_id,name,objective,audience,channel,start_date,budget,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(cid,name,obj,aud,ch,str(start),budget,"Draft",datetime.now().isoformat(timespec="seconds")))
            add_alert(f"Campaign {cid} created"); st.rerun()
        else: st.error("Campaign name and audience are required.")
    st.dataframe(df("campaigns"),use_container_width=True,hide_index=True)

elif page=="Generate Content":
    data=df("campaigns")
    if data.empty: st.warning("Create a campaign first.")
    else:
        campaign=st.selectbox("Campaign",data["name"].tolist()); audience=st.text_input("Audience","iConnect SA customers"); objective=st.selectbox("Objective",["Generate leads","Awareness","Conversions","Engagement"]); channel=st.selectbox("Format",["Email","Social","SMS","Campaign brief"]); offer=st.text_input("Offer / key detail"); tone=st.selectbox("Tone",["Professional","Friendly","Helpful","Energetic"])
        if st.button("Generate draft",type="primary"):
            prompt=f"Create {channel} marketing content for {audience}. Objective: {objective}. Offer: {offer}. Tone: {tone}."
            st.session_state.generated=ai_generate(prompt)
        if "generated" in st.session_state:
            content=st.text_area("Editable draft",st.session_state.generated,height=240)
            if st.button("Submit for approval",type="primary"):
                with db() as c: c.execute("INSERT INTO approvals(campaign,channel,content,status,reviewer,scheduled_date,created_at) VALUES (?,?,?,?,?,?,?)",(campaign,channel,content,"Pending approval","Unassigned","—",datetime.now().isoformat(timespec="seconds")))
                add_alert(f"{campaign} submitted for approval"); st.success("Sent to approval queue.")

elif page=="Schedule & Approvals":
    apps=df("approvals")
    if apps.empty: st.info("No approvals yet.")
    for _,x in apps.iterrows():
        with st.expander(f"{x.campaign} · {x.status}",expanded=True):
            st.write(x.content)
            if x.status=="Pending approval":
                reviewer=st.text_input("Reviewer","Campaign approver",key=f"r{x.id}"); day=st.date_input("Schedule date",date.today()+timedelta(days=1),min_value=date.today(),key=f"d{x.id}")
                c1,c2=st.columns(2)
                if c1.button("Approve & schedule",key=f"a{x.id}"):
                    with db() as c: c.execute("UPDATE approvals SET status=?,reviewer=?,scheduled_date=? WHERE id=?",("Scheduled",reviewer,str(day),int(x.id)))
                    add_alert(f"{x.campaign} scheduled for {day}"); st.rerun()
                if c2.button("Request changes",key=f"n{x.id}"):
                    with db() as c: c.execute("UPDATE approvals SET status=?,reviewer=? WHERE id=?",("Changes requested",reviewer,int(x.id)))
                    add_alert(f"{x.campaign} needs changes"); st.rerun()

elif page=="Report Results":
    st.subheader("Campaign & ROI Reporting")
    st.dataframe(results,use_container_width=True,hide_index=True)
    if not results.empty:
        st.metric("Total leads",int(results["leads"].sum())); st.metric("Total spend",f"R{results["spend"].sum():,.0f}")
        st.bar_chart(results.set_index("campaign")["leads"])

elif page=="Settings":
    st.subheader("Workspace Settings")
    st.success("Authentication is enabled. Secrets are read from Streamlit Secrets first.")
    st.write({"Admin user":admin_user,"Database":"SQLite / PostgreSQL-ready architecture","Current role":st.session_state.get("role")})

elif page=="Integrations":
    st.subheader("Integration Status")
    st.write({"AI provider":"Configured" if secret("OPENAI_API_KEY") else "Not configured","WhatsApp":"Configured" if secret("WHATSAPP_ACCESS_TOKEN") and secret("WHATSAPP_PHONE_NUMBER_ID") else "Not configured","SMTP":"Configured" if secret("SMTP_HOST") else "Not configured","Lead webhook":"Available via webhook.py"})
    st.info("Keep API keys and passwords in Streamlit Secrets. Never commit them to GitHub.")

elif page=="POPIA Consent":
    st.subheader("POPIA Consent Register")
    with st.form("consent"):
        subject=st.text_input("Subject / customer"); channel=st.text_input("Channel"); purpose=st.text_input("Purpose"); status=st.selectbox("Consent status",["Granted","Withdrawn","Pending"]); source=st.text_input("Source"); ok=st.form_submit_button("Record consent",type="primary")
    if ok and subject.strip() and purpose.strip():
        with db() as c: c.execute("INSERT INTO consent_log(subject,channel,purpose,consent_status,source,recorded_by,recorded_at) VALUES (?,?,?,?,?,?,?)",(subject,channel,purpose,status,source,st.session_state.get("user"),datetime.now().isoformat(timespec="seconds")))
        st.success("Consent record saved."); st.rerun()
    st.dataframe(df("consent_log"),use_container_width=True,hide_index=True)
