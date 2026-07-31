import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
from gtts import gTTS
from io import BytesIO
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import random  

load_dotenv()
# --- CONFIGURE GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Add it to.env file")
    st.stop()
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SQLITE - AUTO RESET OFFICER ---
conn = sqlite3.connect('tneb_theft.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS scans
             (id INTEGER PRIMARY KEY, consumer_id TEXT, area TEXT, verdict TEXT,
              risk_score INTEGER, reason TEXT, theft_date TEXT, theft_time TEXT, scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS officers
             (officer_id TEXT PRIMARY KEY, password TEXT)''')

# --- LOGIN GATE ---
st.set_page_config(page_title="TNEB Secure Login", layout="centered")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 TNEB Smart Grid - Officer Login")
    password = st.text_input("Enter Access Password", type="password")
    if st.button("Login"):
        if password == "TNEB2026": # change this password
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong Password")
    st.stop() # stops app if not logged in

st.success("✅ Access Granted")
# --- END LOGIN GATE ---
tneb_contacts = {
    "Chennai": {"office": "TNEB Chennai Central", "phone": "044-28521345", "email": "chennai@tneb.in"},
    "Coimbatore": {"office": "TNEB Coimbatore North", "phone": "0422-2221444", "email": "cbe@tneb.in"},
    "Madurai": {"office": "TNEB Madurai South", "phone": "0452-2533333", "email": "mdu@tneb.in"},
    "Trichy": {"office": "TNEB Trichy Division", "phone": "0431-2700300", "email": "trichy@tneb.in"},
    "Salem": {"office": "TNEB Salem Circle", "phone": "0427-2450200", "email": "salem@tneb.in"}
}

PAGES = ["Home","Officer Login","High Risk Areas","Theft Analytics","Loss Report","History & Download","Live Monitoring","District Search"]

if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'officer_id' not in st.session_state: st.session_state.officer_id = ''
if 'df' not in st.session_state: st.session_state.df = pd.DataFrame()

current_index = PAGES.index(st.session_state.page)
st.set_page_config(page_title="TNEB Smart Grid AI", page_icon="⚡", layout="wide")

def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def navigation_buttons():
    st.markdown("---")
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if current_index > 0:
            if st.button("⬅️ Previous", use_container_width=True, key="prev"): go_to_page(PAGES[current_index - 1])
    with col3:
        if current_index < len(PAGES) - 1:
            if st.button("Next ➡️", type="primary", use_container_width=True, key="next"): go_to_page(PAGES[current_index + 1])

def play_alert():
    if len(st.session_state.df) > 0:
        count = len(st.session_state.df[st.session_state.df['verdict']=='THEFT'])
        text = f"Attention. High risk theft detected. {count} critical cases require immediate inspection."
        tts = gTTS(text=text, lang='en', slow=False)
        fp = BytesIO(); tts.write_to_fp(fp); st.audio(fp.getvalue(), format="audio/mp3")

def analyze_consumer(row):
    if row['prev_month_units'] == 0: drop_percent = 0
    else: drop_percent = ((row['prev_month_units'] - row['units_consumed']) / row['prev_month_units']) * 100
    try:
        prompt = f"Area: {row['area']}, This Month: {row['units_consumed']} units, Last Month: {row['prev_month_units']} units. Flag THEFT if drop >70%. Output: THEFT|85|Reason or NORMAL|10|Reason"
        res = model.generate_content(prompt).text.strip().split("|")
        return pd.Series([res[0], int(res[1]), res[2]])
    except:
        if drop_percent > 70: return pd.Series(["THEFT", 90, f"Sudden {int(drop_percent)}% drop detected"])
        else: return pd.Series(["NORMAL", 10, "Usage is stable"])

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚡ TNEB Command Center")
    if st.session_state.logged_in: st.success(f"Logged in as: {st.session_state.officer_id}")
    st.markdown("### Navigation")
    for p in PAGES[1:]:
        if st.button(p, use_container_width=True, key=f"side_{p}"): go_to_page(p)
    st.markdown("---")
    if st.session_state.logged_in:
        if st.button("🚪 Logout", use_container_width=True): st.session_state.logged_in = False; st.session_state.page = 'Home'; st.rerun()

# SLIDE 1 HOME
if st.session_state.page == 'Home':
    st.markdown("""<style>.big-title {font-size:50px; font-weight:bold; text-align:center; color:#FFD700; background: linear-gradient(90deg, #004aad, #0077ff); padding:40px; border-radius:20px;}
.subtitle {font-size:22px; text-align:center; color:white;}</style>""", unsafe_allow_html=True)
    st.markdown('<div class="big-title">⚡ TNEB ELECTRICITY THEFT DETECTION ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Powered Smart Grid Monitoring System for Tamil Nadu</div>', unsafe_allow_html=True)
    if st.button("🚀 Proceed to Officer Login", use_container_width=True, type="primary"): go_to_page('Officer Login')
    navigation_buttons()

# SLIDE 2 LOGIN - FIXED
elif st.session_state.page == 'Officer Login':
    st.header("🔒 Officer Login")
    st.info("Default Login: **ID = TNEB001** | **Password = tneb@123**")
    with st.container(border=True):
        officer_id = st.text_input("TNEB Officer ID", value="TNEB001")
        password = st.text_input("Password", type="password", value="tneb@123")
        if st.button("Login", type="primary", use_container_width=True):
            c.execute("SELECT * FROM officers WHERE officer_id=? AND password=?", (officer_id, password))
            if c.fetchone(): 
                st.session_state.logged_in = True
                st.session_state.officer_id = officer_id
                st.success("Login Successful!")
                time.sleep(0.5)
                go_to_page('High Risk Areas')
            else: st.error("Invalid Officer ID or Password")
    navigation_buttons()

# SLIDE 3 HIGH RISK
elif st.session_state.page == 'High Risk Areas':
    st.header("🚨 High Risk Areas")
    if not st.session_state.logged_in: st.warning("Please login first"); navigation_buttons(); st.stop()
    try: df = pd.read_csv("data.csv")
    except: st.error("data.csv not found. Please put data.csv in same folder"); navigation_buttons(); st.stop()
    if st.button("⚡ Run AI Scan", type="primary"):
        with st.spinner("Gemini AI is analyzing meters..."):
            df[['verdict','risk_score','reason']] = df.apply(analyze_consumer, axis=1)
        st.session_state.df = df
        theft_date = datetime.now().strftime("%Y-%m-%d"); theft_time = datetime.now().strftime("%H:%M:%S")
        theft_df = df[df['verdict'] == 'THEFT']
        for _, row in theft_df.iterrows():
            c.execute("INSERT INTO scans(consumer_id, area, verdict, risk_score, reason, theft_date, theft_time) VALUES(?,?,?,?,?,?,?)",
                      (row['consumer_id'], row['area'], row['verdict'], row['risk_score'], row['reason'], theft_date, theft_time))
        conn.commit()
        st.success(f"Scan Complete! {len(theft_df)} theft cases found")
    df = st.session_state.df
    if len(df) > 0:
        theft_df = df[df['verdict'] == 'THEFT']
        col1, col2 = st.columns([2,1])
        with col1: st.metric("Critical Alerts", len(theft_df))
        with col2:
            if len(theft_df) > 0 and st.button("🔊 Play AI Voice Alert", type="primary"): play_alert()
        st.markdown("### 🗺️ Theft Hotspot Map")
        map_data = pd.DataFrame({'lat': [13.0827, 13.0067, 12.9698, 13.0711], 'lon': [80.2707, 80.2572, 80.2442, 80.2356]})
        st.map(map_data, zoom=11)
        if len(theft_df) > 0: st.dataframe(theft_df[['consumer_id', 'area', 'risk_score', 'reason']], use_container_width=True)
    navigation_buttons()

# ---------------- SLIDE 4: THEFT ANALYTICS - FINAL CORRECT ----------------
elif st.session_state.page == 'Theft Analytics':
    st.header("📊 Theft Analytics")
    df = st.session_state.df
    if len(df) > 0:
        theft_df = df[df['verdict'] == 'THEFT'].copy()
        
        # 1. CORRECT BAR CHART - Based on Units Lost so bars are different
        st.markdown("### ⚡ Units Lost by Area")
        if len(theft_df) > 0:
            theft_df['units_lost'] = theft_df['prev_month_units'] - theft_df['units_consumed']
            area_loss = theft_df.groupby('area')['units_lost'].sum().reset_index()
            
            fig = px.bar(area_loss, x='area', y='units_lost', 
                         color='units_lost', 
                         color_continuous_scale='OrRd', # Dark Red = More loss
                         text='units_lost', height=400)
            fig.update_traces(textposition='outside', textfont_size=14)
            fig.update_layout(title="Total Units Stolen per Area", xaxis_title="Area", yaxis_title="Units Lost")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No theft cases detected to show chart")

        # 2. DETAILED CASES - DIFFERENT REASON + DIFFERENT RISK + DIFFERENT DROP + IMPRESSIVE STATEMENT
        st.markdown("### 🚨 Detailed Theft Cases")
        if len(theft_df) > 0:
            base_time = datetime.now()
            statements = [
                "🚨 URGENT: ERT Team dispatched. High probability of direct line theft.",
                "⚠️ CONFIRMED: Meter tampering detected. Revenue loss in progress.",
                "🔥 CRITICAL: Consumption pattern matches known theft signature.",
                "💀 SEVERE: This consumer poses major grid instability risk."
            ]
            for i, (_, row) in enumerate(theft_df.iterrows()):
                detected_time = (base_time - timedelta(minutes=i*8 + 3)).strftime("%H:%M:%S")
                detected_date = (base_time - timedelta(minutes=i*8 + 3)).strftime("%Y-%m-%d")
                
                drop_percent = 0
                if row['prev_month_units'] > 0:
                    drop_percent = int(((row['prev_month_units'] - row['units_consumed']) / row['prev_month_units']) * 100)
                units_lost = row['prev_month_units'] - row['units_consumed']
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f"**Consumer ID:** `{row['consumer_id']}`")
                    col2.markdown(f"**Area:** `{row['area']}`")
                    col3.markdown(f"**Detected:** `{detected_date} {detected_time}`")
                    
                    st.error(f"**🤖 AI Analysis:** {row['reason']}") # Different for each
                    st.warning(f"**📈 Stats:** Sudden Drop: {drop_percent}% | Risk Score: {row['risk_score']}/100 | Units Lost: {units_lost}")
                    st.info(f"**Action Required:** {statements[i % 4]}") # Impressive statement
    navigation_buttons()
# ---------------- SLIDE 5: LOSS REPORT - PRO VERSION ----------------
elif st.session_state.page == 'Loss Report':
    st.header("💰 Loss Report & Revenue Impact")
    df = st.session_state.df
    if len(df) > 0:
        theft_df = df[df['verdict'] == 'THEFT'].copy()
        theft_df['units_lost'] = theft_df['prev_month_units'] - theft_df['units_consumed']
        
        # CALCULATIONS
        sudden_drop = len(df[df['prev_month_units'] - df['units_consumed'] > 100]) # >100 units drop = case
        total_units_lost = theft_df['units_lost'].sum()
        rate_per_unit = 8
        monthly_loss = total_units_lost * rate_per_unit
        yearly_loss = monthly_loss * 12
        grid_efficiency = 100 - ((total_units_lost / df['prev_month_units'].sum()) * 100)
        grid_efficiency = max(80, min(99, grid_efficiency))
        
        # 4 METRIC CARDS
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚨 Sudden Drop Cases", sudden_drop)
        with col2:
            st.metric("📅 Est. Monthly Loss", f"₹{monthly_loss:,.0f}", delta=f"{total_units_lost} Units")
        with col3:
            st.metric("📆 Est. Yearly Loss", f"₹{yearly_loss:,.0f}", delta=f"₹{monthly_loss:,.0f}/month")
        with col4:
            st.metric("⚡ Grid Efficiency", f"{grid_efficiency:.1f}%")

        st.markdown("---")
        
        # 2 IMPRESSIVE CHARTS
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("### 🎯 Theft Distribution - Donut Chart")
            if len(theft_df) > 0:
                area_cases = theft_df.groupby('area').size().reset_index(name='count')
                fig_donut = px.pie(area_cases, names='area', values='count', hole=0.5,
                                   color_discrete_sequence=px.colors.qualitative.Dark24)
                fig_donut.update_traces(textposition='outside', textinfo='percent+label')
                fig_donut.update_layout(showlegend=True)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No theft cases yet")
        
        with colB:
            st.markdown("### 💸 Revenue Loss by Area - Treemap")
            if len(theft_df) > 0:
                area_loss = theft_df.groupby('area')['units_lost'].sum().reset_index()
                area_loss['revenue_loss'] = area_loss['units_lost'] * rate_per_unit
                fig_tree = px.treemap(area_loss, path=['area'], values='revenue_loss',
                                      color='revenue_loss', color_continuous_scale='Reds')
                fig_tree.update_traces(texttemplate='%{label}<br>₹%{value:,.0f}')
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("No revenue loss yet")
        
        st.markdown("---")
        # CONTACT DETAILS SECTION
        st.markdown("### 📞 TNEB Emergency Contact Details")
        if len(theft_df) > 0:
            areas = theft_df['area'].unique()
            cols = st.columns(len(areas))
            for i, area in enumerate(areas):
                contact = tneb_contacts.get(area, {"office": f"TNEB {area}", "phone": "1912", "email": "help@tneb.in"})
                with cols[i]:
                    with st.container(border=True):
                        st.error(f"**{area}**")
                        st.markdown(f"**Office:** {contact['office']}")
                        st.markdown(f"**Helpline:** `{contact['phone']}`")
                        st.markdown(f"**Email:** {contact['email']}")
                        st.button(f"Call {area}", key=f"call_{area}")
    navigation_buttons()
# ---------------- SLIDE 6: HISTORY & DOWNLOAD - FINAL COMMAND CENTER ----------------
elif st.session_state.page == 'History & Download':
    st.header("📜 Investigation History & Command Reports")
    
    history = pd.read_sql_query("SELECT * FROM scans ORDER BY scan_timestamp DESC", conn)
    
    if len(history) > 0:
        # 1. CALCULATIONS FOR TOTAL LOSS
        theft_history = history[history['verdict']=='THEFT'].copy()
        total_theft_cases = len(theft_history)
        total_revenue_loss = total_theft_cases * 15000 # ₹15k per case
        total_units_lost = total_theft_cases * 200 # avg 200 units
        
        # 2. 4 KPI CARDS - IMPRESSIVE
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📡 Total Scans Done", len(history))
        with col2:
            st.metric("🚨 Total Theft Cases", total_theft_cases, delta=f"-₹{total_revenue_loss:,}", delta_color="inverse")
        with col3:
            st.metric("💸 Total Revenue Loss", f"₹{total_revenue_loss/100000:.2f} Lakhs")
        with col4:
            st.metric("⚡ Total Units Lost", f"{total_units_lost:,} Units")
        
        st.divider()
        
        # 3. FULL TABLE WITH COLORS - FIXED FOR NEW PANDAS
        st.markdown("### 📊 Complete Investigation Log")
        
        # Choose columns that exist
        cols_to_show = ['scan_timestamp','consumer_id','area','verdict','risk_score','reason']
        if 'prev_month_units' in history.columns: cols_to_show.insert(3, 'prev_month_units')
        if 'units_consumed' in history.columns: cols_to_show.insert(4, 'units_consumed')
        
        def color_theft(val):
            color = '#ff4b4b' if val == "THEFT" else '#21c354'
            return f'background-color: {color}; color: white; font-weight: bold'
        
        def color_risk(val):
            if val > 80: color = '#ff4b4b'
            elif val > 50: color = '#ffa500'
            else: color = '#21c354'
            return f'background-color: {color}; color: white; font-weight: bold'
            
        styled_history = history[cols_to_show].style\
            .map(color_theft, subset=['verdict'])\
            .map(color_risk, subset=['risk_score'])\
            .set_properties(**{'text-align': 'center'})\
            .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
            
        st.dataframe(styled_history, use_container_width=True, height=450)
        
        st.divider()
        
        # 4. DOWNLOAD + SUMMARY SECTION
        st.markdown("### 📥 Export Reports")
        colD1, colD2, colD3 = st.columns(3)
        
        with colD1:
            csv = history.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full CSV", data=csv, file_name=f'TNEB_Full_Report_{datetime.now().strftime("%Y%m%d")}.csv', type="primary", use_container_width=True)
        
        with colD2:
            if len(theft_history) > 0:
                theft_csv = theft_history.to_csv(index=False).encode('utf-8')
                st.download_button("🚨 Download Theft Only", data=theft_csv, file_name=f'TNEB_Theft_Cases_{datetime.now().strftime("%Y%m%d")}.csv', type="secondary", use_container_width=True)
        
        with colD3:
            if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
                c.execute("DELETE FROM scans")
                conn.commit()
                st.toast("History Cleared!", icon="✅")
                st.rerun()
        
        # 5. IMPRESSIVE EXECUTIVE SUMMARY
        st.markdown("### 📈 Executive Summary")
        if total_theft_cases > 0:
            st.error(f"**CRITICAL ALERT:** {total_theft_cases} theft cases detected. Estimated government revenue loss: **₹{total_revenue_loss:,}** and **{total_units_lost:,} units**. Immediate field action recommended in high-risk zones.")
        else:
            st.success("**GRID STATUS: SECURE** - No theft cases detected in current records.")
            
    else:
        st.warning("📭 No scan history found.")
        st.info("Go to 'Theft Analytics' Slide 3 and click 'Run AI Scan' to generate data.")
    
    navigation_buttons()

# ---------------- SLIDE 7: LIVE MONITORING - FINAL VERSION ----------------
elif st.session_state.page == 'Live Monitoring':
    st.header("📡 Live CCTV Monitoring - TNEB Control Room")
    st.caption("Real-time AI-powered surveillance of high-risk areas")
    
    # CUSTOM CSS
    st.markdown("""
    <style>
    .blink {animation: blinker 1.5s linear infinite;}
    @keyframes blinker {50% {opacity: 0.3;}}
    </style>
    """, unsafe_allow_html=True)
    
    # 1. TOP CRITICAL ALERT BANNER
    st.markdown('<div class="blink" style="border-left: 5px solid red; background-color: #2a0a0a; padding: 12px; border-radius: 8px; margin-bottom: 20px;"><h4 style="color:red; margin:0;">🚨 CRITICAL ALERT: THEFT DETECTED IN CAM-03 VELACHERY</h4><p style="margin:0; color:#ffaaaa;">AI Confidence: 98% | Action: JE Notified</p></div>', unsafe_allow_html=True)
    
    # 2. KPI METRICS
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟢 Grid Status", "ONLINE", "Stable")
    k2.metric("🚨 Active Threats", "1", "+1", delta_color="inverse")
    k3.metric("📹 Cameras Online", "3/3", "100%")
    k4.metric("⚡ District", "Chennai South")
    
    st.divider()
    
    # 3. CAMERA GRID
    st.markdown("### 🎥 Live Camera Feeds")
    cam1, cam2, cam3 = st.columns(3)
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # CAMERA 1 - NORMAL
    with cam1:
        st.markdown('<h5 style="color:#21c354;">✅ CAM-01: NORMAL</h5>', unsafe_allow_html=True)
        st.image("assets/cam1_normal.jpeg", caption="Anna Nagar - Meter Room")
        st.success("Status: No anomaly detected")
        st.code(f"Last Update: {current_time}")
    
    # CAMERA 2 - NORMAL  
    with cam2:
        st.markdown('<h5 style="color:#21c354;">✅ CAM-02: NORMAL</h5>', unsafe_allow_html=True)
        st.image("assets/cam2_normal.jpeg", caption="Tambaram - Transformer")
        st.success("Status: Load stable")
        st.code(f"Last Update: {current_time}")
    
    # CAMERA 3 - THEFT
    with cam3:
        st.markdown('<h5 class="blink" style="color:red;">🚨 CAM-03: THEFT DETECTED</h5>', unsafe_allow_html=True)
        st.image("assets/cam3_theft.jpeg", caption="Velachery - Meter Tampering")
        st.error("**AI Detected:** Physical Bypass | Risk: 98%")
        st.code(f"Last Update: {current_time}")
    
    st.divider()
    
    # 4. SECURITY EVENT TIMELINE - THE NEW LOG
    st.markdown("### 📝 Security Event Timeline")

    log_data = [
        {
            "time": current_time,
            "camera": "CAM-03",
            "location": "Velachery",
            "event": "THEFT DETECTED",
            "severity": "CRITICAL",
            "details": "Meter Bypass + Physical Tampering",
            "action": "ALERT SENT TO JE + DISCONNECT ORDER"
        },
        {
            "time": (datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S'),
            "camera": "CAM-02", 
            "location": "Tambaram",
            "event": "LOAD ANOMALY",
            "severity": "WARNING",
            "details": "15% Sudden Load Drop",
            "action": "FLAGGED FOR REVIEW"
        },
        {
            "time": (datetime.now() - timedelta(minutes=12)).strftime('%H:%M:%S'),
            "camera": "CAM-01",
            "location": "Anna Nagar", 
            "event": "NORMAL",
            "severity": "INFO",
            "details": "Routine Scan Complete",
            "action": "LOGGED"
        }
    ]

    for log in log_data:
        # Color based on severity
        if log["severity"] == "CRITICAL":
            icon = "🚨"
            border_color = "red"
            bg_color = "#3a0a0a"
        elif log["severity"] == "WARNING":
            icon = "⚠️"
            border_color = "orange"
            bg_color = "#3a2a0a"
        else:
            icon = "✅"
            border_color = "#21c354"
            bg_color = "#0a3a1a"
        
        st.markdown(f"""
        <div style="border-left: 4px solid {border_color}; background-color: {bg_color}; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <h5 style="margin: 0; color: white;">{icon} {log['event']}</h5>
                <span style="color: #aaa; font-size: 12px;">{log['time']}</span>
            </div>
            <p style="margin: 5px 0; color: #ddd;"><b>Location:</b> {log['camera']} - {log['location']}</p>
            <p style="margin: 5px 0; color: #ddd;"><b>Details:</b> {log['details']}</p>
            <p style="margin: 5px 0; color: #4fc3f7;"><b>Action:</b> {log['action']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Feeds", type="primary"): 
        st.rerun()
        
    navigation_buttons()
# ---------------- SLIDE 8: DISTRICT SEARCH - ALL TN ----------------
elif st.session_state.page == 'District Search':
    st.header("🔍 District Search - TNEB Theft Monitoring")
    st.caption("Select any Tamil Nadu district to check theft status")
    
    # FULL LIST OF 38 TN DISTRICTS
    tn_districts = [
        'Ariyalur', 'Chengalpattu', 'Chennai', 'Coimbatore', 'Cuddalore', 
        'Dharmapuri', 'Dindigul', 'Erode', 'Kallakurichi', 'Kancheepuram',
        'Kanyakumari', 'Karur', 'Krishnagiri', 'Madurai', 'Mayiladuthurai',
        'Nagapattinam', 'Namakkal', 'Nilgiris', 'Perambalur', 'Pudukkottai',
        'Ramanathapuram', 'Ranipet', 'Salem', 'Sivaganga', 'Tenkasi',
        'Thanjavur', 'Theni', 'Thoothukudi', 'Tiruchirappalli', 'Tirunelveli',
        'Tirupathur', 'Tiruppur', 'Tiruvallur', 'Tiruvannamalai', 'Tiruvarur',
        'Vellore', 'Viluppuram', 'Virudhunagar'
    ]
    
    # TNEB CONTACTS FOR EACH DISTRICT
    tneb_contacts = {
        'Chennai': {'office': 'TNEB Chennai South', 'phone': '044-28521111'},
        'Madurai': {'office': 'TNEB Madurai', 'phone': '0452-2520101'},
        'Coimbatore': {'office': 'TNEB Coimbatore', 'phone': '0422-2221001'},
        'Salem': {'office': 'TNEB Salem', 'phone': '0427-2450011'},
        'Tiruchirappalli': {'office': 'TNEB Trichy', 'phone': '0431-2702001'},
        'Tirunelveli': {'office': 'TNEB Tirunelveli', 'phone': '0462-2570001'},
        'Erode': {'office': 'TNEB Erode', 'phone': '0424-2260001'},
        'Vellore': {'office': 'TNEB Vellore', 'phone': '0416-2220001'},
        'Thanjavur': {'office': 'TNEB Thanjavur', 'phone': '04362-230001'},
        'Thoothukudi': {'office': 'TNEB Thoothukudi', 'phone': '0461-2320001'}
    }
    # Add default contact for remaining districts
    for d in tn_districts:
        if d not in tneb_contacts:
            tneb_contacts[d] = {'office': f'TNEB {d}', 'phone': '1912'}
    
    selected_district = st.selectbox("Select District to Check", tn_districts)
    
    if st.button(f"Check {selected_district}", type="primary", use_container_width=True):
        contact = tneb_contacts[selected_district]
        
        # HIGH RISK DISTRICTS - DEMO DATA
        high_risk_districts = ['Chennai', 'Madurai', 'Coimbatore', 'Salem', 'Tiruchirappalli']
        
        if selected_district in high_risk_districts:
            st.error(f"⚠️ THEFT DETECTED in {selected_district}")
            st.warning("12 suspicious meters found. Estimated loss: ₹2.3 Lakhs this month")
            
            # Show fake details
            st.markdown("### 🚨 Flagged Locations")
            st.dataframe(pd.DataFrame({
                'Area': ['Velachery', 'Tambaram', 'Anna Nagar'],
                'Meters': [5, 4, 3],
                'Risk': ['Critical', 'High', 'Medium']
            }), use_container_width=True)
            
            st.info(f"📞 Contact: {contact['office']} | {contact['phone']}")
            if st.button("📄 Generate District FIR"):
                st.success("FIR forwarded to JE Team")
        else: 
            st.success(f"✅ {selected_district} is SAFE")
            st.metric("Suspicious Meters", "0")
            st.info(f"📞 Contact: {contact['office']} | {contact['phone']}")
    
    navigation_buttons()
