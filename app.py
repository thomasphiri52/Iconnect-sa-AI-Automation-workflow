import os, random, hashlib, hmac
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from db import init_db, db, rows, add_activity, add_alert, get_user, ensure_admin, add_audit, setting, set_setting
from integrations import ai_generate, send_email, send_whatsapp

st.set_page_config(page_title='iConnect SA AI Automation', page_icon='🤖', layout='wide')

# Production-safe login defaults: configure ICONNECT_ADMIN_USER and ICONNECT_ADMIN_PASSWORD
# in Streamlit secrets/environment before deployment.
st.markdown('''<style>.stApp{background:linear-gradient(135deg,#080d1a,#101a32)} section[data-testid="stSidebar"]{background:#0b1224} div[data-testid="stMetric"]{background:#121c32;border:1px solid #263654;padding:14px;border-radius:12px}.card{background:#121c32;border:1px solid #263654;border-radius:12px;padding:16px;margin-bottom:10px}</style>''', unsafe_allow_html=True)

LEAD_STAGES=['New','Contacted','Qualified','Proposal','Won','Lost']; LEAD_SOURCES=['Website','WhatsApp','Email','Social','Campaign','Referral','Customer Service','Manual']; PRODUCTS=['Fibre','Business Internet','VoIP','Cloud','Managed Services','General']
PAGES=['Overview','Lead / CRM','AI Customer Service','Ticket Queue','Alerts & Activity','Plan Campaigns','Generate Content','Schedule & Approvals','Report Results','Settings','Integrations','POPIA Consent']
ROLE_PAGES={'viewer':['Overview','AI Customer Service','Ticket Queue','Alerts & Activity','Report Results'],'agent':['Overview','Lead / CRM','AI Customer Service','Ticket Queue','Alerts & Activity','Plan Campaigns','Generate Content','Schedule & Approvals','Report Results'],'manager':PAGES,'admin':PAGES}

@st.cache_resource
def boot(): init_db(); return True
boot()
ensure_admin(os.getenv('ICONNECT_ADMIN_USER','admin'), os.getenv('ICONNECT_ADMIN_PASSWORD','change-me'))

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def authenticate():
    if st.session_state.get('auth'): return True
    st.sidebar.title('🤖 iConnect SA'); st.sidebar.caption('Secure workspace login')
    user=st.sidebar.text_input('Username')
    pw=st.sidebar.text_input('Password',type='password')
    if st.sidebar.button('Sign in',type='primary'):
        account=get_user(user)
        if account and hmac.compare_digest(account['password_hash'],hash_pw(pw)):
            st.session_state.auth=True; st.session_state.user=user; st.session_state.role=account['role']; add_audit(user,'login'); st.rerun()
        else: st.sidebar.error('Invalid credentials.')
    st.title('iConnect SA | Secure workspace'); st.info('Configure ICONNECT_ADMIN_USER and ICONNECT_ADMIN_PASSWORD before deployment.'); st.stop()

authenticate()

def df(table): return pd.DataFrame(rows(table))
def lead_score(stage, product, source, value, has_contact):
    s=35+{'New':0,'Contacted':10,'Qualified':25,'Proposal':30,'Won':40,'Lost':-30}.get(stage,0)+{'Business Internet':12,'Managed Services':15,'Cloud':10,'Fibre':8,'VoIP':7}.get(product,0)+{'Referral':12,'WhatsApp':8,'Campaign':7,'Website':5,'Customer Service':5}.get(source,0)+min(15,int(float(value or 0)/5000))+(5 if has_contact else 0); return max(0,min(100,s))
def classify(m):
    t=m.lower()
    for words,cat,p,team in [(('down','outage','offline'),'Connectivity','High','Network Ops'),(('slow','latency'),'Connectivity','Medium','Network Ops'),(('voip','call','phone'),'Voice','High','Voice Support'),(('invoice','billing','payment'),'Billing','Low','Billing'),(('password','login'),'Account access','Medium','Service Desk')]:
        if any(w in t for w in words): return cat,p,team
    return 'General enquiry','Medium','Service Desk'
def makecopy(ch,aud,obj,offer,tone):
    extra=(' '+offer) if offer else ''
    if ch=='Email': return f'Subject: Stay connected with iConnect SA\n\nHi there,\nDiscover solutions designed for {aud}. Objective: {obj}.{extra}\nContact our team to explore your options.\n\nThe iConnect SA Team'
    if ch=='Social': return f'Stay connected. Keep moving! For {aud}, discover solutions built around the way you work.{extra} Contact iConnect SA. #iConnectSA #StayConnected'
    if ch=='SMS': return f'iConnect SA: {offer or "Explore connectivity options built for you."} Contact our team. Reply STOP to opt out.'
    return f'Campaign brief\nAudience: {aud}\nObjective: {obj}\nMessage: Stay connected with iConnect SA.{extra}\nTone: {tone}\nCTA: Contact our team.'

def navigate(target): st.session_state.page=target; st.rerun()
if 'page' not in st.session_state: st.session_state.page='Overview'
st.sidebar.title('🤖 iConnect SA'); st.sidebar.caption(f"AI Automation Control Room · {st.session_state.get('user','admin')} · {st.session_state.get('role','viewer')}")
allowed=ROLE_PAGES.get(st.session_state.get('role','viewer'),ROLE_PAGES['viewer'])
page=st.sidebar.radio('Navigation',allowed,index=allowed.index(st.session_state.page) if st.session_state.page in allowed else 0); st.session_state.page=page
if st.sidebar.button('Sign out'): add_audit(st.session_state.get('user'),'logout'); st.session_state.clear(); st.rerun()
st.title('iConnect SA | AI Automation'); st.caption('CRM · customer service · campaigns · approvals · reporting')

leads=df('leads'); campaigns=df('campaigns'); tickets=df('tickets'); results=df('results')
if page=='Overview':
    a,b,c,d,e=st.columns(5); active=leads[~leads.stage.isin(['Won','Lost'])] if not leads.empty else leads
    a.metric('Open tickets',len(tickets[tickets.status!='Resolved'])); b.metric('Active leads',len(active)); c.metric('Qualified leads',len(leads[leads.stage.isin(['Qualified','Proposal'])])); d.metric('Pipeline value',f"R{active.value.sum():,.0f}"); e.metric('Reported leads',int(results.leads.sum()) if not results.empty else 0)
    st.subheader('Quick actions'); qs=st.columns(5)
    for col,label,target in zip(qs,['👥 Open CRM','🎧 Customer Service','🎫 Ticket Queue','📣 Plan Campaign','📊 Reports'],['Lead / CRM','AI Customer Service','Ticket Queue','Plan Campaigns','Report Results']):
        if col.button(label,use_container_width=True): navigate(target)
    l,r=st.columns(2)
    with l:
        st.subheader('Lead pipeline'); x=leads.stage.value_counts().reindex(LEAD_STAGES,fill_value=0).reset_index(); x.columns=['Stage','Leads']; st.bar_chart(x.set_index('Stage'))
    with r:
        st.subheader('Pipeline value'); pv=leads.groupby('stage',as_index=True)['value'].sum() if not leads.empty else pd.Series(dtype=float); st.bar_chart(pv)
    st.subheader('Campaign results'); st.dataframe(results,use_container_width=True,hide_index=True)

elif page=='Lead / CRM':
    st.subheader('Lead & CRM Control Room'); tabs=st.tabs(['Pipeline','Add lead','Lead details','Activity & export'])
    with tabs[0]:
        if leads.empty: st.info('No leads yet.')
        else: st.dataframe(leads[['lead_id','name','company','email','phone','product','source','stage','score','owner','value','next_followup','notes']],use_container_width=True,hide_index=True)
    with tabs[1]:
        with st.form('addlead'):
            c1,c2=st.columns(2); name=c1.text_input('Contact name *'); company=c2.text_input('Company'); email=c1.text_input('Email'); phone=c2.text_input('Phone / WhatsApp'); product=c1.selectbox('Product',PRODUCTS); source=c2.selectbox('Source',LEAD_SOURCES); stage=c1.selectbox('Stage',LEAD_STAGES); owner=c2.text_input('Owner','Sales Team'); value=c1.number_input('Deal value (R)',min_value=0.0,step=500.0); follow=c2.date_input('Next follow-up',date.today()+timedelta(days=2),min_value=date.today()); notes=st.text_area('Notes'); ok=st.form_submit_button('Create lead',type='primary')
        if ok:
            if not name.strip() or not(email.strip() or phone.strip()): st.error('Name and email/phone are required.')
            else:
                lid=f'LEAD-{random.randint(1000,9999)}'; score=lead_score(stage,product,source,value,bool(email or phone)); now=datetime.now().isoformat(timespec='seconds')
                with db() as c: c.execute('INSERT INTO leads(lead_id,name,company,email,phone,product,source,stage,score,owner,value,last_contact,next_followup,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(lid,name,company,email,phone,product,source,stage,score,owner,value,str(date.today()) if stage!='New' else '—',str(follow),notes,now))
                add_activity('Lead created',lid); st.success(f'{lid} created with score {score}/100.'); st.rerun()
    with tabs[2]:
        if not leads.empty:
            sel=st.selectbox('Select lead',leads.lead_id.tolist()); row=leads[leads.lead_id==sel].iloc[0]; idx=int(row.id)
            with st.form('editlead'):
                ns=st.selectbox('Stage',LEAD_STAGES,index=LEAD_STAGES.index(row.stage)); no=st.text_input('Owner',row.owner); np=st.selectbox('Product',PRODUCTS,index=PRODUCTS.index(row.product) if row.product in PRODUCTS else 0); nv=st.number_input('Value (R)',min_value=0.0,value=float(row.value),step=500.0); nf=st.date_input('Next follow-up',pd.to_datetime(row.next_followup).date() if row.next_followup!='—' else date.today()+timedelta(days=2)); nn=st.text_area('Notes',row.notes); save=st.form_submit_button('Save changes',type='primary')
            if save:
                score=lead_score(ns,np,row.source,nv,bool(row.email or row.phone));
                with db() as c: c.execute('UPDATE leads SET stage=?,owner=?,product=?,value=?,next_followup=?,notes=?,score=? WHERE id=?',(ns,no,np,nv,str(nf),nn,score,idx))
                add_activity(f'Lead updated to {ns}',sel); st.success('Lead updated.'); st.rerun()
    with tabs[3]:
        act=df('activity'); st.dataframe(act,use_container_width=True,hide_index=True); st.download_button('Download CRM CSV',leads.to_csv(index=False).encode(),'iconnect_crm_leads.csv','text/csv')

elif page=='AI Customer Service':
    msg=st.text_area('Customer message')
    if st.button('Analyse enquiry',type='primary') and msg.strip(): st.session_state.triage={'msg':msg,'result':classify(msg)}
    if 'triage' in st.session_state:
        x=st.session_state.triage; cat,p,team=x['result']; a,b,c=st.columns(3); a.metric('Category',cat); b.metric('Priority',p); c.metric('Team',team); st.text_area('Suggested reply',f'Thanks for contacting iConnect SA. Our {team} team will review your {cat.lower()} enquiry. Never send passwords or OTPs.')
        if st.button('Create ticket & alert',type='primary'):
            tid=f'IC-{random.randint(2000,9999)}'; now=datetime.now().isoformat(timespec='seconds');
            with db() as c: c.execute('INSERT INTO tickets(ticket_id,issue,priority,status,team,created_at) VALUES (?,?,?,?,?,?)',(tid,msg,p,'Open',team,now))
            add_alert(f'{tid} routed to {team}'); st.success(f'{tid} created and routed to {team}.'); st.rerun()

elif page=='Ticket Queue':
    st.subheader('Ticket Queue'); tickets=df('tickets'); st.dataframe(tickets,use_container_width=True,hide_index=True)
    if not tickets.empty:
        tid=st.selectbox('Ticket',tickets.ticket_id.tolist()); new=st.selectbox('Update status',['Open','In progress','Resolved']);
        if st.button('Update ticket'):
            with db() as c: c.execute('UPDATE tickets SET status=? WHERE ticket_id=?',(new,tid))
            add_alert(f'{tid} status changed to {new}'); st.rerun()

elif page=='Alerts & Activity':
    st.subheader('Alerts'); st.dataframe(df('alerts'),use_container_width=True,hide_index=True); st.subheader('CRM activity'); st.dataframe(df('activity'),use_container_width=True,hide_index=True)

elif page=='Plan Campaigns':
    with st.form('campaign'):
        name=st.text_input('Campaign name'); obj=st.selectbox('Objective',['Generate leads','Awareness','Conversions','Engagement','Retention']); aud=st.text_input('Target audience'); ch=st.selectbox('Channel',['Email','Social','SMS','Website','Multi-channel']); start=st.date_input('Start date',date.today()+timedelta(days=7),min_value=date.today()); budget=st.number_input('Budget (R)',min_value=0.0,step=500.0); ok=st.form_submit_button('Create campaign',type='primary')
    if ok:
        if name.strip() and aud.strip():
            cid=f'CMP-{random.randint(100,999)}';
            with db() as c: c.execute('INSERT INTO campaigns(campaign_id,name,objective,audience,channel,start_date,budget,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)',(cid,name,obj,aud,ch,str(start),budget,'Draft',datetime.now().isoformat(timespec='seconds')))
            add_alert(f'Campaign {cid} created'); st.rerun()
        else: st.error('Campaign name and audience are required.')
    st.dataframe(df('campaigns'),use_container_width=True,hide_index=True)

elif page=='Generate Content':
    campaigns=df('campaigns');
    if campaigns.empty: st.warning('Create a campaign first.')
    else:
        with st.form('content'):
            campaign=st.selectbox('Campaign',campaigns.name.tolist()); aud=st.text_input('Audience','iConnect SA customers'); obj=st.selectbox('Objective',['Generate leads','Awareness','Conversions','Engagement']); ch=st.selectbox('Format',['Email','Social','SMS','Campaign brief']); offer=st.text_input('Offer / key detail'); tone=st.selectbox('Tone',['Professional','Friendly','Helpful','Energetic']); go=st.form_submit_button('Generate draft',type='primary')
        if go: st.session_state.generated={'Campaign':campaign,'Channel':ch,'Content':makecopy(ch,aud,obj,offer,tone)}
        if 'generated' in st.session_state:
            content=st.text_area('Editable draft',st.session_state.generated['Content'],height=220)
            if st.button('Submit for approval',type='primary'):
                with db() as c: c.execute('INSERT INTO approvals(campaign,channel,content,status,reviewer,scheduled_date,created_at) VALUES (?,?,?,?,?,?,?)',(st.session_state.generated['Campaign'],st.session_state.generated['Channel'],content,'Pending approval','Unassigned','—',datetime.now().isoformat(timespec='seconds')))
                add_alert(f"{st.session_state.generated['Campaign']} submitted for approval"); st.success('Sent to approval queue.'); st.rerun()

elif page=='Schedule & Approvals':
    apps=df('approvals')
    if apps.empty: st.info('No approvals yet.')
    for _,x in apps.iterrows():
        with st.expander(f"{x.campaign} · {x.status}",expanded=True):
            st.write(x.content)
            if x.status=='Pending approval':
                reviewer=st.text_input('Reviewer','Campaign approver',key=f'r{x.id}'); day=st.date_input('Schedule date',date.today()+timedelta(days=1),min_value=date.today(),key=f'd{x.id}')
                c1,c2=st.columns(2)
                if c1.button('Approve & schedule',key=f'a{x.id}'):
                    with db() as c: c.execute('UPDATE approvals SET status=?,reviewer=?,scheduled_date=? WHERE id=?',('Scheduled',reviewer,str(day),int(x.id)))
                    add_alert(f'{x.campaign} scheduled for {day}'); st.rerun()
                if c2.button('Request changes',key=f'n{x.id}'):
                    with db() as c: c.execute('UPDATE approvals SET status=?,reviewer=? WHERE id=?',('Changes requested',reviewer,int(x.id)))
                    add_alert(f'{x.campaign} needs changes'); st.rerun()

elif page=='Report Results':
    st.subheader('Campaign & Business Results'); st.dataframe(results,use_container_width=True,hide_index=True)
    if not results.empty:
        a,b,c,d=st.columns(4); a.metric('Leads',int(results.leads.sum())); b.metric('Conversions',int(results.conversions.sum())); c.metric('Spend',f"R{results.spend.sum():,.0f}"); d.metric('Revenue',f"R{results.revenue.sum():,.0f}")
        st.bar_chart(results.set_index('campaign')[['leads','conversions']])

elif page=='Settings':
    st.subheader('System Settings')
    st.info('For production, set secrets/environment variables in Streamlit Cloud. Do not store passwords in source code.')
    st.write('Admin user:', os.getenv('ICONNECT_ADMIN_USER','admin'))
    st.write('Password configured:', 'Yes' if os.getenv('ICONNECT_ADMIN_PASSWORD') else 'No — set ICONNECT_ADMIN_PASSWORD')
    st.write('Database:', setting('database_path','iconnect.db'))

elif page=='Integrations':
    st.subheader('Integrations'); st.write('AI:', 'Configured' if os.getenv('OPENAI_API_KEY') else 'Not configured'); st.write('Email:', 'Configured' if os.getenv('SMTP_HOST') else 'Not configured'); st.write('WhatsApp:', 'Configured' if os.getenv('WHATSAPP_TOKEN') else 'Not configured')

elif page=='POPIA Consent':
    st.subheader('POPIA Consent Register'); st.write('Capture consent before marketing communications and retain an auditable record.');
    with st.form('consent'):
        lead=st.text_input('Lead / contact ID'); purpose=st.text_input('Purpose','Marketing communications'); channel=st.selectbox('Channel',['Email','SMS','WhatsApp','Phone']); granted=st.checkbox('Consent granted'); ok=st.form_submit_button('Save consent',type='primary')
    if ok and lead.strip():
        with db() as c: c.execute('INSERT INTO consent(contact_id,purpose,channel,granted_at,revoked_at) VALUES (?,?,?,?,?)',(lead,purpose,channel,datetime.now().isoformat(timespec='seconds') if granted else None,None))
        add_audit(st.session_state.get('user','admin'),f'consent {lead}: {granted}'); st.success('Consent record saved.'); st.rerun()
    st.dataframe(df('consent'),use_container_width=True,hide_index=True)
