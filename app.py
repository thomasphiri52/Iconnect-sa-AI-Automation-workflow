import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="iConnect SA AI Automation", page_icon="🤖", layout="wide")

st.markdown("""
<style>
:root { --blue:#1769e0; --navy:#102a43; --bg:#f5f9ff; }
.stApp { background: var(--bg); }
.block-container { padding-top: 1.5rem; }
h1,h2,h3 { color: var(--navy); }
.metric-card { background:white; padding:18px; border-radius:14px; border:1px solid #dbe7f5; box-shadow:0 2px 10px rgba(20,60,100,.05); }
.workflow { background:white; padding:20px; border-radius:16px; border:1px solid #dbe7f5; }
.step { padding:16px; border-radius:12px; min-height:150px; background:#fff; border:1px solid #dbe7f5; }
.impact { background:linear-gradient(135deg,#0f3558,#1769e0); color:white; padding:22px; border-radius:16px; }
.small { color:#5c7895; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("# 📊 iConnect SA")
st.sidebar.caption("AI Automation • Smarter Marketing • Bigger Results")
page = st.sidebar.radio("Navigate", [
    "Dashboard","AI Command Centre","Lead Intelligence","Campaign Automation",
    "AI Content Studio","CRM Automation","Customer Intelligence","Analytics & ROI"
])
st.sidebar.divider()
st.sidebar.markdown("### Channels")
for c in ["💬 WhatsApp","✉️ Email","📱 SMS","📣 Social Media","🌐 Website"]:
    st.sidebar.write(c)

st.title("iConnect SA AI Automation Platform")
st.caption("From data to customers — fully automated.")

# KPI cards
cols = st.columns(5)
kpis = [
    ("Total Leads","1,248","↑ 32%","More qualified leads"),
    ("Qualified Leads","462","↑ 48%","Higher quality prospects"),
    ("Campaign Revenue","R 284,750","↑ 56%","Better campaign performance"),
    ("Total Sales","124","↑ 41%","More conversions"),
    ("ROI","4.8x","↑ 63%","Higher return on investment"),
]
for col,(name,value,delta,note) in zip(cols,kpis):
    with col:
        st.markdown(f"""<div class="metric-card"><b>{name}</b><h2>{value}</h2>
        <span style="color:#159447">{delta}</span><br><span class="small">{note}</span></div>""",
                    unsafe_allow_html=True)

st.write("")
st.subheader("🤖 AI Automation Workflow")
st.caption("A connected intelligence loop from data collection to measurable business growth.")

steps = [
("1. Data Sources","🌐 Website\n📣 Social Media\n💬 CRM\n📧 Ads & Email\n📝 Customer enquiries"),
("2. AI Data Engine","Collect\nClean\nClassify\nEnrich"),
("3. iConnect AI Brain","Customer insights\nLead scoring\nSentiment analysis\nCampaign recommendations\nSales predictions"),
("4. Automation Engine","Lead → CRM → Follow-up\nCampaign → AI content → Launch\nCustomer → Personalised offer\nAlert → Sales team"),
("5. Omnichannel","WhatsApp\nEmail\nSMS\nSocial Media\nWeb"),
("6. Results & ROI","More leads\nMore sales\nHigher revenue\nBetter ROAS\nCustomer retention"),
]
wcols = st.columns(6)
for col,(title,body) in zip(wcols,steps):
    with col:
        st.markdown(f'<div class="step"><h4>{title}</h4><div style="white-space:pre-line">{body}</div></div>', unsafe_allow_html=True)

st.success("🔄 AI Learning Loop: every interaction feeds performance data back into the intelligence layer.")

if page == "Dashboard":
    a,b,c = st.columns([1.2,1.5,1])
    with a:
        st.subheader("🎯 Lead Pipeline")
        df = pd.DataFrame({"Stage":["New Leads","Qualified","Proposal","Won"],"Count":[724,462,186,124]})
        st.bar_chart(df.set_index("Stage"))
        st.info("AI Lead Scoring: top 124 leads have an estimated 82% conversion probability.")
    with b:
        st.subheader("📈 Campaign Performance")
        days = ["Sep 30","Oct 1","Oct 2","Oct 3","Oct 4","Oct 5","Oct 6"]
        chart = pd.DataFrame({
            "Reach":[6000,8000,9500,11000,14500,15000,17000],
            "Clicks":[2500,3100,3900,4700,6500,7200,9300],
            "Conversions":[900,1100,1400,1800,2200,2500,2900]}, index=days)
        st.line_chart(chart)
    with c:
        st.subheader("💡 AI Recommendations")
        recs = [
            ("Increase WhatsApp campaign budget","3.2x higher conversion rate this week."),
            ("Follow up with 138 hot leads",">80% intent score."),
            ("Create a special offer","Target customers inactive for 30+ days."),
            ("Adjust campaign schedule","Audience is most active 7–9 PM.")
        ]
        for title,desc in recs:
            st.markdown(f"**{title}**  \n<span class='small'>{desc}</span>", unsafe_allow_html=True)
            st.button("Apply", key=title)

    st.write("")
    st.markdown('<div class="impact"><h2>🚀 iConnect SA Business Impact</h2><p>How the platform creates measurable business value.</p></div>', unsafe_allow_html=True)
    impact_cols = st.columns(5)
    impacts = [
        ("💰","Increase Revenue","Convert more qualified opportunities into customers."),
        ("🎯","Improve Marketing ROI","Automatically optimise campaigns toward what performs."),
        ("⚙️","Reduce Manual Work","Automate repetitive marketing, CRM and follow-up tasks."),
        ("⚡","Faster Lead Response","AI qualifies and routes leads immediately."),
        ("❤️","Improve Customer Experience","Personalised communication across channels."),
        ("📊","Better Decisions","Real-time AI insights for management."),
        ("📈","Scale Marketing","Run more campaigns without proportional workload."),
        ("🧠","Build Intelligence","Continuously learn from customer and campaign data."),
        ("🏆","Competitive Advantage","Become more data-driven and AI-enabled."),
        ("🔄","Continuous Optimisation","Performance feeds back into the AI learning loop.")
    ]
    for i,(icon,title,desc) in enumerate(impacts):
        with impact_cols[i%5]:
            st.markdown(f"""<div class="metric-card" style="margin-top:12px"><h3>{icon} {title}</h3>
            <span class="small">{desc}</span></div>""", unsafe_allow_html=True)

elif page == "AI Command Centre":
    st.subheader("🧠 AI Command Centre")
    st.write("Prioritise the actions most likely to improve growth.")
    actions = pd.DataFrame({
        "Priority":["High","High","Medium","Medium","Low"],
        "AI Action":["Follow up hot leads","Optimise WhatsApp budget","Re-engage inactive customers","Refresh ad creative","Review low-ROI segment"],
        "Expected impact":["+12% conversion","+18% campaign ROI","+8% retention","+10% CTR","Reduce wasted spend"]
    })
    st.dataframe(actions, use_container_width=True, hide_index=True)

elif page == "Lead Intelligence":
    st.subheader("🎯 Lead Intelligence")
    n = st.slider("Number of leads to simulate", 50, 500, 150)
    rng=np.random.default_rng(42)
    leads=pd.DataFrame({
        "Lead": [f"Lead {i+1}" for i in range(n)],
        "Intent Score": rng.integers(35,100,n),
        "Engagement": rng.integers(20,100,n),
        "Channel": rng.choice(["WhatsApp","Website","Facebook","Email"],n)
    })
    leads["AI Priority"]=pd.cut(leads["Intent Score"],[0,59,79,100],labels=["Low","Medium","Hot"])
    st.dataframe(leads.sort_values("Intent Score",ascending=False).head(25),use_container_width=True,hide_index=True)

elif page == "Campaign Automation":
    st.subheader("📣 Campaign Automation")
    campaign=st.selectbox("Campaign",["Summer Deals","Lead Nurture","Reactivation","New Customer Offer"])
    objective=st.selectbox("Objective",["Conversions","Lead generation","Retention","Awareness"])
    channels=st.multiselect("Channels",["WhatsApp","Email","SMS","Facebook","Instagram"],["WhatsApp","Email"])
    if st.button("🤖 Generate AI Campaign Plan",type="primary"):
        st.success(f"AI plan generated for **{campaign}**: optimise for **{objective}** across {', '.join(channels)}.")
        st.write("Recommended sequence: Segment → Generate content → Launch → Score engagement → Optimise → Report ROI.")

elif page == "AI Content Studio":
    st.subheader("✍️ AI Content Studio")
    prompt=st.text_area("Campaign brief","Create a promotional message for a high-intent customer segment.")
    tone=st.selectbox("Tone",["Professional","Friendly","Urgent","Premium"])
    if st.button("Generate Content",type="primary"):
        st.markdown(f"""### AI Draft
**{tone}**
> Discover an offer designed for you. Our AI identified that this is the right time to reconnect. Explore the latest iConnect SA opportunity today and take the next step with confidence.
""")

elif page == "CRM Automation":
    st.subheader("🔄 CRM Automation")
    st.checkbox("Automatically create CRM record for new lead",True)
    st.checkbox("Send personalised first follow-up",True)
    st.checkbox("Escalate high-intent leads to sales",True)
    st.checkbox("Schedule follow-up when no response",True)
    st.checkbox("Log campaign outcome automatically",True)
    st.info("Workflow status: **Active** — 5 automations running.")

elif page == "Customer Intelligence":
    st.subheader("👥 Customer Intelligence")
    seg = pd.DataFrame({"Segment":["High Value","Active","At Risk","New","Inactive"],"Customers":[182,426,118,214,308]})
    st.bar_chart(seg.set_index("Segment"))
    st.write("AI insight: prioritise high-value and at-risk customers for personalised journeys.")

elif page == "Analytics & ROI":
    st.subheader("📊 Analytics & ROI")
    spend=st.number_input("Campaign spend (R)",1000,1000000,60000,step=5000)
    revenue=st.number_input("Attributed revenue (R)",1000,5000000,284750,step=5000)
    roi=(revenue-spend)/spend
    c1,c2,c3=st.columns(3)
    c1.metric("Spend",f"R {spend:,.0f}")
    c2.metric("Revenue",f"R {revenue:,.0f}")
    c3.metric("ROI",f"{roi:.2f}x")
    st.progress(min(1, roi/10),text="AI ROI health score")

st.divider()
st.caption("iConnect SA • AI-Powered Marketing • Automated Workflows • Real Business Growth")
