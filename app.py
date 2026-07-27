import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from io import BytesIO

load_dotenv()

# --- CONFIGURE GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Add it to a.env file")
    st.stop()
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- REAL BACKEND: SQLITE ---
conn = sqlite3.connect('tneb_theft.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS scans
             (id INTEGER PRIMARY KEY, consumer_id TEXT, area TEXT, verdict TEXT, 
              risk_score INTEGER, reason TEXT, theft_date TEXT, theft_time TEXT, scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS officers
             (officer_id TEXT PRIMARY KEY, password TEXT)''')
# Add default officer if not exists
c.execute("INSERT OR IGNORE INTO officers VALUES('TNEB001', 'tneb@123')")
conn.commit()

# TNEB District Contact Database - KEPT SAME
tneb_contacts = {
    "Chennai": {"office": "TNEB Chennai Central", "phone": "044-28521345", "email": "chennai@tneb.in"},
    "Coimbatore": {"office": "TNEB Coimbatore North", "phone": "0422-2221444", "email": "cbe@tneb.in"},
    "Madurai": {"office": "TNEB Madurai South", "phone": "0452-2533333", "email": "mdu@tneb.in"},
    "Trichy": {"office": "TNEB Trichy Division", "phone": "0431-2700300", "email": "trichy@tneb.in"},
    "Salem": {"office": "TNEB Salem Circle", "phone": "0427-2450200", "email": "salem@tneb.in"},
    "Tirunelveli": {"office": "TNEB Tirunelveli", "phone": "0462-2575000", "email": "tvl@tneb.in"},
    "Erode": {"office": "TNEB Erode", "phone": "0424-2261000", "email": "erode@tneb.in"},
    "Vellore": {"office": "TNEB Vellore", "phone": "0416-2222444", "email": "vellore@tneb.in"},
    "Thoothukudi": {"office": "TNEB Thoothukudi", "phone": "0461-2323333", "email": "tdy@tneb.in"},
    "Dindigul": {"office": "TNEB Dindigul", "phone": "0451-2431000", "email": "dgl@tneb.in"},
    "Thanjavur": {"office": "TNEB Thanjavur", "phone": "04362-230000", "email": "tjore@tneb.in"},
    "Ranipet": {"office": "TNEB Ranipet", "phone": "04172-244444", "email": "ranipet@tneb.in"},
    "Sivaganga": {"office": "TNEB Sivaganga", "phone": "04575-240000", "email": "sivaganga@tneb.in"},
    "Kanniyakumari": {"office": "TNEB Nagercoil", "phone": "04652-222", "email": "nagercoil@tneb.in"},
    "Tiruppur": {"office": "TNEB Tiruppur", "phone": "0421-2200000", "email": "tirupur@tneb.in"},
    "Pudukkottai": {"office": "TNEB Pudukkottai", "phone": "04322-222", "email": "pdk@tneb.in"},
    "Nagapattinam": {"office": "TNEB Nagapattinam", "phone": "04365-242222", "email": "ngp@tneb.in"},
    "Namakkal": {"office": "TNEB Namakkal", "phone": "04286-280000", "email": "namakkal@tneb.in"},
    "Dharmapuri": {"office": "TNEB Dharmapuri", "phone": "04342-230000", "email": "dharmapuri@tneb.in"},
    "Cuddalore": {"office": "TNEB Cuddalore", "phone": "04142-230000", "email": "cuddalore@tneb.in"}
}

# --- SESSION STATE FOR PAGES ---
if 'page' not in st.session_state:
    st.session_state.page = 'intro'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'officer_id' not in st.session_state:
    st.session_state.officer_id = ''

st.set_page_config(page_title="TNEB Smart Grid AI", page_icon="⚡", layout="wide")

# --- PAGE 1: SLIDE INTRO ---
if st.session_state.page == 'intro':
    st.markdown("""
    <style>
   .big-title {font-size:50px; font-weight:bold; text-align:center; color:#FFD700; background: linear-gradient(90deg, #004aad, #0077ff); padding:40px; border-radius:20px;}
   .subtitle {font-size:22px; text-align:center; color:white;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="big-title">⚡ TNEB ELECTRICITY THEFT DETECTION ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Powered Smart Grid Monitoring System for Tamil Nadu</div>', unsafe_allow_html=True)
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/3e/TNEB_Logo.png", width=200) # TNEB Logo
    st.markdown("###")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Proceed to Officer Login", use_container_width=True, type="primary"):
            st.session_state.page = 'login'
            st.rerun()

# --- PAGE 2: OFFICER LOGIN ---
elif st.session_state.page == 'login':
    st.title("🔒 TNEB Officer Login")
    st.info("Only authorized TNEB officers can access the theft detection system")
    
    with st.form("login_form"):
        officer_id = st.text_input("TNEB Officer ID")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            c.execute("SELECT * FROM officers WHERE officer_id=? AND password=?", (officer_id, password))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.officer_id = officer_id
                st.session_state.page = 'dashboard'
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Officer ID or Password")
    
    if st.button("⬅ Back to Intro"):
        st.session_state.page = 'intro'
        st.rerun()

# --- PAGE 3: MAIN DASHBOARD - ALL YOUR CODE + NEW FEATURES ---
elif st.session_state.page == 'dashboard' and st.session_state.logged_in:
    st.sidebar.success(f"Logged in as: {st.session_state.officer_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = 'intro'
        st.rerun()
    
    st.title("⚡ TNEB AI Theft Detection System")
    st.subheader("Smart Grid Monitoring for Tamil Nadu")
    st.info("This AI analyzes smart meter data to detect abnormal usage patterns and flag potential electricity theft.")
    st.markdown("---")
    st.write(f"🕒 Live Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- LOAD DATA --- KEPT SAME
    try:
        df = pd.read_csv("data.csv")
    except FileNotFoundError:
        st.error("data.csv not found. Please upload your data file to the same folder.")
        st.stop()

    def analyze_consumer(row):
        if row['prev_month_units'] == 0: 
            drop_percent = 0
        else:
            drop_percent = ((row['prev_month_units'] - row['units_consumed']) / row['prev_month_units']) * 100

        prompt = f"""
        You are a TNEB analyst. Analyze this data:
        Area: {row['area']}, This Month: {row['units_consumed']} units, Last Month: {row['prev_month_units']} units, Meter Age: {row['meter_age_years']} yrs
        Rules: Flag THEFT if drop >70% or very low with old meter.
        Output ONLY as: THEFT|85|Sudden 77% drop, possible bypass
        If normal: NORMAL|10|Usage is stable
        """
        try:
            res = model.generate_content(prompt).text.strip()
            parts = res.split("|")
            return pd.Series([parts[0], int(parts[1]), parts[2]])
        except:
            if drop_percent > 70 or (row['units_consumed'] < 50 and row['meter_age_years'] > 5):
                return pd.Series(["THEFT", 90, f"Sudden {int(drop_percent)}% drop detected"])
            else:
                return pd.Series(["NORMAL", 10, "Usage is stable"])

    # --- MAIN BUTTON LOGIC --- KEPT SAME + ADDED DB SAVE + DATE/TIME
    if st.button("⚡ Run AI Scan", type="primary"):
        with st.spinner("Gemini AI is analyzing meters..."):
            df[['verdict','risk_score','reason']] = df.apply(analyze_consumer, axis=1)

        theft_df = df[df['verdict'] == 'THEFT']
        theft_date = datetime.now().strftime("%Y-%m-%d")
        theft_time = datetime.now().strftime("%H:%M:%S")

        # SAVE TO REAL BACKEND
        for _, row in theft_df.iterrows():
            c.execute("INSERT INTO scans(consumer_id, area, verdict, risk_score, reason, theft_date, theft_time) VALUES(?,?,?,?,?,?,?)",
                      (row['consumer_id'], row['area'], row['verdict'], row['risk_score'], row['reason'], theft_date, theft_time))
        conn.commit()

        # LIVE ALERT + TNEB CONTACT SYSTEM - KEPT SAME
        if len(theft_df) > 0:
            st.error(f"🚨 ALERT: {len(theft_df)} Potential Theft Cases Detected! Immediate Action Required.")
            with st.expander("Click to see high risk cases + TNEB Contact"):
                for i in range(min(5, len(theft_df))):
                    row = theft_df.iloc[i]
                    area = row['area']
                    contact = tneb_contacts.get(area, {"office": "TNEB Helpline", "phone": "1912", "email": "support@tneb.in"})
                    st.warning(f"⚡ **Case {i+1}**: {row['consumer_id']} | Area: {area} | Risk: {row['risk_score']}% | Time: {theft_time}")
                    st.info(f"📞 **Contact TNEB {area}**\n\n**Office:** {contact['office']}\n**Phone:** {contact['phone']}\n**Email:** {contact['email']}")
                    st.markdown("---")
        else:
            st.success("✅ No theft detected. Grid is safe.")

        st.subheader("📍 Risk by Area") # KEPT SAME
        area_risk = df.groupby('area')['risk_score'].mean().reset_index()
        fig = px.bar(area_risk, x='area', y='risk_score', color='risk_score', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🚨 Flagged Cases") # KEPT SAME + ADDED DATE/TIME
        if len(theft_df) > 0:
            for _, row in theft_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['consumer_id']} - {row['area']}** | Risk: {row['risk_score']}/100")
                    st.write(f"Usage: {row['prev_month_units']} → {row['units_consumed']} units")
                    st.write(f"🗓️ Theft Date: {theft_date} | ⏰ Time: {theft_time}")
                    st.info(f"AI Reason: {row['reason']}")
        else:
            st.info("No flagged cases to show.")

        st.markdown("### 📊 Impact Dashboard") # KEPT SAME
        col1, col2, col3 = st.columns(3)
        col1.metric("Theft Cases Detected", len(theft_df), "+8%")
        col2.metric("Estimated Loss Prevented", "₹4.2 Lakhs", "+15%")
        col3.metric("Grid Efficiency", "94%", "+3%")

    # --- EXTRA WOW FEATURE 1: SCAN HISTORY FROM DB ---
    st.markdown("### 📜 Scan History from Database")
    history = pd.read_sql_query("SELECT * FROM scans ORDER BY scan_timestamp DESC LIMIT 20", conn)
    st.dataframe(history, use_container_width=True)
    
    # --- EXTRA WOW FEATURE 2: EXPORT TO EXCEL ---
    if st.button("📥 Export History to Excel"):
        history.to_excel("theft_history.xlsx", index=False)
        st.success("Exported as theft_history.xlsx")

    # --- EXTRA WOW FEATURE 3: PDF REPORT ---
    def create_pdf(df):
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, 800, "TNEB Theft Detection Report")
        p.setFont("Helvetica", 10)
        y = 770
        for _, row in df.iterrows():
            p.drawString(50, y, f"{row['consumer_id']} | {row['area']} | {row['verdict']} | {row['theft_date']} {row['theft_time']}")
            y -= 20
            if y < 50: break
        p.save()
        buffer.seek(0)
        return buffer
    
    if len(history) > 0:
        pdf = create_pdf(history)
        st.download_button("📄 Download PDF Report", data=pdf, file_name="TNEB_Report.pdf", mime="application/pdf")

    # ALL YOUR OTHER CHARTS KEPT SAME
    st.markdown("### 📈 Sample Risk Comparison")
    chart_data = pd.DataFrame({'Area': ['T.Nagar', 'Adyar', 'Velachery', 'Nungambakkam'],'Risk Score': [85, 45, 72, 30]})
    st.bar_chart(chart_data.set_index('Area'))

    st.markdown("### 🗺️ Theft Hotspot Map")
    map_data = pd.DataFrame({'lat': [13.0827, 13.0067, 12.9698, 13.0711],'lon': [80.2707, 80.2572, 80.2442, 80.2356],'Area': ['T.Nagar', 'Adyar', 'Velachery', 'Nungambakkam'],'Risk': [85, 45, 72, 30]})
    high_risk_map = map_data[map_data['Risk'] > 50]
    if len(high_risk_map) > 0:
        st.warning(f"Showing {len(high_risk_map)} High-Risk Zones in Chennai")
        st.map(high_risk_map[['lat', 'lon']], zoom=11)
    else:
        st.success("No high-risk zones detected")

    st.markdown("### 🔍 District Search") # KEPT SAME
    tn_districts = ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem', 'Tirunelveli',
    'Erode', 'Vellore', 'Thoothukudi', 'Dindigul', 'Thanjavur', 'Ranipet',
    'Sivaganga', 'Virudhunagar', 'Kanniyakumari', 'Tiruppur', 'Kancheepuram',
    'Tiruvallur', 'Cuddalore', 'Nagapattinam', 'Karur', 'Namakkal', 'Krishnagiri']
    selected_district = st.selectbox("Select District to Check", tn_districts)
    if st.button(f"Check {selected_district}"):
        high_risk_districts = ['Chennai', 'Madurai', 'Coimbatore', 'Tirunelveli']
        if selected_district in high_risk_districts:
            st.error(f"⚠️ THEFT DETECTED in {selected_district}")
            st.warning("12 suspicious meters found. Estimated loss: ₹2.3 Lakhs")
        else:
            st.success(f"✅ {selected_district} is SAFE")
